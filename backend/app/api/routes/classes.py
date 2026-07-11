"""Class management — create, connect bot, manage students"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.class_group import ClassGroup
from app.services.student_service import StudentService

router = APIRouter(prefix="/classes", tags=["Classes"])


class CreateClassRequest(BaseModel):
    name: str
    description: Optional[str] = None
    bot_token: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    wird_time: str = "07:00"
    timezone: str = "Asia/Riyadh"
    reminders_enabled: bool = True
    reminder_1_hours: str = "2"
    reminder_2_hours: str = "6"
    reminder_3_time: str = "21:00"


@router.get("/")
def list_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classes = db.query(ClassGroup).filter(
        ClassGroup.teacher_id == current_user.id,
        ClassGroup.is_active == True,
    ).all()
    return [_class_to_dict(c) for c in classes]


@router.post("/")
def create_class(
    req: CreateClassRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = ClassGroup(
        name=req.name,
        description=req.description,
        teacher_id=current_user.id,
        bot_token=req.bot_token,
        telegram_chat_id=req.telegram_chat_id,
        wird_time=req.wird_time,
        timezone=req.timezone,
        reminders_enabled=req.reminders_enabled,
        reminder_1_hours=req.reminder_1_hours,
        reminder_2_hours=req.reminder_2_hours,
        reminder_3_time=req.reminder_3_time,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _class_to_dict(c)


@router.get("/{class_id}")
def get_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = _get_class_or_404(class_id, current_user.id, db)
    return _class_to_dict(c)


@router.put("/{class_id}")
def update_class(
    class_id: str,
    req: CreateClassRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = _get_class_or_404(class_id, current_user.id, db)
    for field, val in req.dict(exclude_unset=True).items():
        setattr(c, field, val)
    db.commit()
    db.refresh(c)
    return _class_to_dict(c)


@router.delete("/{class_id}")
def delete_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = _get_class_or_404(class_id, current_user.id, db)
    c.is_active = False
    db.commit()
    return {"status": "deleted"}


@router.get("/{class_id}/students")
def list_students(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_class_or_404(class_id, current_user.id, db)
    svc = StudentService(db)
    students = svc.get_class_students(class_id)
    return [
        {
            "id": str(s.id),
            "full_name": s.full_name,
            "telegram_username": s.telegram_username,
            "telegram_id": s.telegram_id,
            "current_streak": s.current_streak,
            "longest_streak": s.longest_streak,
            "total_completed": s.total_completed,
            "total_missed": s.total_missed,
            "completion_percentage": s.completion_percentage,
            "joined_at": s.joined_at.isoformat(),
        }
        for s in students
    ]


@router.post("/{class_id}/set-webhook")
async def set_webhook(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register Telegram webhook for this class's bot."""
    from telegram import Bot
    from app.core.config import settings

    c = _get_class_or_404(class_id, current_user.id, db)
    if not c.bot_token:
        raise HTTPException(status_code=400, detail="لا يوجد Bot Token")

    webhook_url = f"{settings.backend_url}/api/telegram/webhook/{class_id}"
    bot = Bot(token=c.bot_token)
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.telegram_webhook_secret,
        allowed_updates=["message", "callback_query", "chat_member"],
    )
    return {"status": "webhook set", "url": webhook_url}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_class_or_404(class_id: str, teacher_id, db: Session) -> ClassGroup:
    c = db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.teacher_id == teacher_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")
    return c


def _class_to_dict(c: ClassGroup) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "telegram_chat_id": c.telegram_chat_id,
        "telegram_chat_title": c.telegram_chat_title,
        "wird_time": c.wird_time,
        "timezone": c.timezone,
        "reminders_enabled": c.reminders_enabled,
        "reminder_1_hours": c.reminder_1_hours,
        "reminder_2_hours": c.reminder_2_hours,
        "reminder_3_time": c.reminder_3_time,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat(),
    }
