"""Daily Wird routes — create, schedule, send"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.class_group import ClassGroup
from app.services.wird_service import WirdService

router = APIRouter(prefix="/wird", tags=["Daily Wird"])


class CreateWirdRequest(BaseModel):
    class_id: str
    wird_date: date
    title: str
    content: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    motivational_message: Optional[str] = None
    wird_type: str = "quran"
    is_holiday: bool = False


@router.post("/")
def create_wird(
    req: CreateWirdRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_class_owner(req.class_id, current_user.id, db)
    svc = WirdService(db)
    wird = svc.create_wird(
        class_id=req.class_id,
        wird_date=req.wird_date,
        title=req.title,
        content=req.content,
        file_url=req.file_url,
        file_type=req.file_type,
        motivational=req.motivational_message,
        wird_type=req.wird_type,
    )
    return _wird_to_dict(wird)


@router.get("/{class_id}/today")
def get_today(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = WirdService(db)
    wird = svc.get_today_wird_by_class(class_id)
    if not wird:
        return None
    return _wird_to_dict(wird)


@router.get("/{class_id}/history")
def get_history(
    class_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = WirdService(db)
    wirds = svc.get_history(class_id, days)
    return [_wird_to_dict(w) for w in wirds]


@router.post("/{wird_id}/send-now")
async def send_now(
    wird_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger sending a wird immediately."""
    from telegram import Bot
    from app.telegram.bot import send_daily_wird
    from app.models.daily_wird import DailyWird

    wird = db.query(DailyWird).filter(DailyWird.id == wird_id).first()
    if not wird:
        raise HTTPException(status_code=404, detail="الورد غير موجود")

    class_obj = wird.class_group
    if not class_obj.bot_token or not class_obj.telegram_chat_id:
        raise HTTPException(status_code=400, detail="Bot Token أو Chat ID غير مضبوطين")

    bot = Bot(token=class_obj.bot_token)
    msg_id = await send_daily_wird(
        bot=bot,
        chat_id=class_obj.telegram_chat_id,
        wird_id=str(wird.id),
        title=wird.title,
        content=wird.content,
        file_url=wird.file_url,
        file_type=wird.file_type,
        motivational=wird.motivational_message,
    )

    svc = WirdService(db)
    svc.mark_sent(wird_id, msg_id)
    return {"status": "sent", "telegram_message_id": msg_id}


def _verify_class_owner(class_id: str, teacher_id, db: Session):
    c = db.query(ClassGroup).filter(
        ClassGroup.id == class_id, ClassGroup.teacher_id == teacher_id
    ).first()
    if not c:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية")


def _wird_to_dict(w) -> dict:
    return {
        "id": str(w.id),
        "class_id": str(w.class_id),
        "wird_date": w.wird_date.isoformat(),
        "title": w.title,
        "content": w.content,
        "file_url": w.file_url,
        "file_type": w.file_type,
        "wird_type": w.wird_type,
        "status": w.status,
        "sent_at": w.sent_at.isoformat() if w.sent_at else None,
        "telegram_message_id": w.telegram_message_id,
        "is_holiday": w.is_holiday,
    }
