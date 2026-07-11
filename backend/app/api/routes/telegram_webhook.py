"""
Telegram Webhook endpoint.
Each class has its own webhook: POST /api/telegram/webhook/{class_id}
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.class_group import ClassGroup
from app.telegram.bot import create_application
from telegram import Update

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])

# Cache: class_id -> Application
_apps: dict = {}


def _get_app(class_id: str, bot_token: str):
    if class_id not in _apps:
        _apps[class_id] = create_application(bot_token)
    return _apps[class_id]


@router.post("/webhook/{class_id}")
async def telegram_webhook(
    class_id: str,
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
):
    # Verify secret
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db = SessionLocal()
    try:
        class_obj = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not class_obj or not class_obj.bot_token:
            raise HTTPException(status_code=404, detail="Class not found")

        bot_token = class_obj.bot_token
    finally:
        db.close()

    app = _get_app(class_id, bot_token)

    data = await request.json()
    async with app:
        update = Update.de_json(data, app.bot)
        await app.process_update(update)

    return {"ok": True}
