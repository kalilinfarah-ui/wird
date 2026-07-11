"""Auth routes — Telegram Login + email/password"""
import hashlib
import hmac
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.db.database import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TelegramLoginData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _verify_telegram_hash(data: TelegramLoginData) -> bool:
    """Validate Telegram Login Widget data."""
    secret = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
    check_string = "\n".join([
        f"auth_date={data.auth_date}",
        f"first_name={data.first_name}",
        f"id={data.id}",
        *([ f"last_name={data.last_name}"] if data.last_name else []),
        *([ f"photo_url={data.photo_url}"] if data.photo_url else []),
        *([ f"username={data.username}"] if data.username else []),
    ])
    computed = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if computed != data.hash:
        return False
    if time.time() - data.auth_date > 86400:
        return False
    return True


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")

    user = User(
        full_name=req.full_name,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=UserRole.TEACHER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _make_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطل")
    return _make_token_response(user)


@router.post("/telegram", response_model=TokenResponse)
def telegram_login(data: TelegramLoginData, db: Session = Depends(get_db)):
    if not _verify_telegram_hash(data):
        raise HTTPException(status_code=401, detail="بيانات تيليغرام غير صحيحة")

    user = db.query(User).filter(User.telegram_id == data.id).first()
    if not user:
        user = User(
            full_name=f"{data.first_name} {data.last_name or ''}".strip(),
            telegram_id=data.id,
            telegram_username=data.username,
            telegram_photo_url=data.photo_url,
            role=UserRole.TEACHER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.telegram_username = data.username
        user.telegram_photo_url = data.photo_url
        db.commit()

    return _make_token_response(user)


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="رمز التحديث غير صالح")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}


def _make_token_response(user: User) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "telegram_id": user.telegram_id,
            "telegram_username": user.telegram_username,
        },
    }
