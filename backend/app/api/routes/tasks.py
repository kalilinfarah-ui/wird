"""
External Cron Task Endpoints
============================
These endpoints replace APScheduler completely.
cron-job.org (free) calls them at the right times.

All endpoints require the header:
    X-Cron-Secret: <CRON_SECRET from .env>

cron-job.org setup:
  /tasks/send-wird      → daily at wird_time (e.g., 07:00)
  /tasks/send-reminders → every 5 minutes (handles reminder 1, 2, 3 automatically)
  /tasks/send-summary   → once per day in the evening (e.g., 22:00)

The /health endpoint (no auth) is pinged every 5 min by UptimeRobot to keep
Render's free service awake.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from telegram import Bot

from app.core.config import settings
from app.db.database import get_db, SessionLocal
from app.models.class_group import ClassGroup
from app.models.daily_wird import DailyWird, WirdStatus
from app.models.reminder import Reminder, ReminderStatus
from app.services.attendance_service import AttendanceService
from app.services.wird_service import WirdService
from app.telegram.bot import send_daily_wird
from app.telegram.teacher_commands import _build_summary_text
from app.utils.timezone import is_wird_time, local_date, utc_datetime_from_local_hhmm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Cron Tasks"])


# ─── Auth guard ───────────────────────────────────────────────────────────────

def _verify_secret(x_cron_secret: str = Header(default="")):
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")


# ─── /tasks/send-wird ─────────────────────────────────────────────────────────

@router.post("/send-wird")
async def send_wird_task(
    _: None = Depends(_verify_secret),
    db: Session = Depends(get_db),
):
    """
    Called by cron-job.org every minute from 00:00–23:59.
    Sends today's wird to any class whose scheduled LOCAL time matches *now* (±1 min).
    Each class stores its own timezone (e.g. Africa/Algiers), so Algerian classes
    fire at 07:00 Algiers time regardless of when UTC is.
    """
    now_utc = datetime.utcnow()
    now_hhmm = now_utc.strftime("%H:%M")
    classes = db.query(ClassGroup).filter(
        ClassGroup.is_active == True,
        ClassGroup.telegram_chat_id.isnot(None),
        ClassGroup.bot_token.isnot(None),
    ).all()

    sent = []
    skipped = []

    for cls in classes:
        tz = cls.timezone or "UTC"
        # Compare scheduled HH:MM against the class's LOCAL time, not UTC
        if not is_wird_time(cls.wird_time, tz, tolerance_minutes=1):
            skipped.append(cls.name)
            continue

        # Use the class's local date for wird lookup
        today_local = local_date(tz)
        wird_svc = WirdService(db)
        today_wird = wird_svc.get_today_wird_by_class(str(cls.id), today_local)

        if not today_wird:
            logger.warning(f"No wird scheduled for {cls.name} on {date.today()}")
            skipped.append(cls.name)
            continue

        if today_wird.status == WirdStatus.SENT:
            skipped.append(cls.name)
            continue

        if today_wird.is_holiday:
            skipped.append(cls.name)
            continue

        try:
            bot = Bot(token=cls.bot_token)
            msg_id = await send_daily_wird(
                bot=bot,
                chat_id=cls.telegram_chat_id,
                wird_id=str(today_wird.id),
                title=today_wird.title,
                content=today_wird.content,
                file_url=today_wird.file_url,
                file_type=today_wird.file_type,
                motivational=today_wird.motivational_message,
            )
            wird_svc.mark_sent(str(today_wird.id), msg_id)
            _schedule_reminders_for(db, today_wird, cls, tz)
            sent.append(cls.name)
            logger.info(f"Sent wird to {cls.name} ({cls.telegram_chat_id}) [tz={tz}]")
        except Exception as e:
            logger.exception(f"Failed to send wird to {cls.name}")

    return {"sent": sent, "skipped_count": len(skipped), "time": now_hhmm}


# ─── /tasks/send-reminders ────────────────────────────────────────────────────

@router.post("/send-reminders")
async def send_reminders_task(
    _: None = Depends(_verify_secret),
    db: Session = Depends(get_db),
):
    """
    Called by cron-job.org every 5 minutes.
    Sends any pending reminder whose scheduled_at has passed.
    """
    now = datetime.utcnow()
    pending = db.query(Reminder).filter(
        Reminder.status == ReminderStatus.PENDING,
        Reminder.scheduled_at <= now,
    ).all()

    results = []
    att_svc = AttendanceService(db)

    for reminder in pending:
        cls = reminder.class_group
        if not cls or not cls.bot_token or not cls.telegram_chat_id:
            reminder.status = ReminderStatus.SKIPPED
            db.commit()
            continue

        if not cls.reminders_enabled:
            reminder.status = ReminderStatus.SKIPPED
            db.commit()
            continue

        pending_students = att_svc.get_pending_students(
            str(cls.id), str(reminder.daily_wird_id)
        )

        if not pending_students:
            reminder.status = ReminderStatus.SKIPPED
            db.commit()
            results.append({"class": cls.name, "reminder": reminder.reminder_number, "status": "skipped_all_done"})
            continue

        try:
            bot = Bot(token=cls.bot_token)
            count = len(pending_students)

            await bot.send_message(
                chat_id=cls.telegram_chat_id,
                text=(
                    f"⏰ *تذكير {reminder.reminder_number}*\n\n"
                    f"لا يزال *{count}* {'طالب' if count == 1 else 'طلاب'} "
                    f"لم {'يكمل' if count == 1 else 'يكملوا'} ورد اليوم.\n\n"
                    f"اضغطوا على رسالة الورد وسجّلوا حضوركم ✅"
                ),
                parse_mode="Markdown",
            )
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = now
            reminder.recipients_count = count
            db.commit()
            results.append({"class": cls.name, "reminder": reminder.reminder_number, "sent_to": count})
        except Exception as e:
            logger.error(f"Failed reminder {reminder.id}: {e}")
            reminder.status = ReminderStatus.FAILED
            db.commit()

    return {"processed": len(pending), "results": results}


# ─── /tasks/send-summary ──────────────────────────────────────────────────────

@router.post("/send-summary")
async def send_summary_task(
    _: None = Depends(_verify_secret),
    db: Session = Depends(get_db),
):
    """
    Called once per day (e.g., 22:00) by cron-job.org.
    Posts a group recap: who completed, who didn't, and the daily rate.
    """
    classes = db.query(ClassGroup).filter(
        ClassGroup.is_active == True,
        ClassGroup.telegram_chat_id.isnot(None),
        ClassGroup.bot_token.isnot(None),
    ).all()

    sent = []
    att_svc = AttendanceService(db)

    for cls in classes:
        try:
            summary = _build_summary_text(cls, att_svc, db)
            bot = Bot(token=cls.bot_token)
            await bot.send_message(
                chat_id=cls.telegram_chat_id,
                text=summary,
                parse_mode="Markdown",
            )
            sent.append(cls.name)
        except Exception as e:
            logger.error(f"Failed summary for {cls.name}: {e}")

    return {"sent": sent}


# ─── Helper: schedule reminders after wird is sent ───────────────────────────

def _schedule_reminders_for(db: Session, wird: DailyWird, cls: ClassGroup, tz: str):
    """
    Create Reminder rows (UTC datetimes) so /tasks/send-reminders picks them up.

    Reminders 1 & 2 are relative (hours after wird send, calculated from UTC now).
    Reminder 3 is an absolute LOCAL time (e.g. 21:00 Algiers) → converted to UTC.
    """
    from app.models.reminder import Reminder, ReminderStatus

    now_utc = datetime.utcnow()
    slots = [
        (1, now_utc + timedelta(hours=int(cls.reminder_1_hours))),
        (2, now_utc + timedelta(hours=int(cls.reminder_2_hours))),
    ]

    # Reminder 3: fixed local time → convert to UTC correctly for the class timezone
    r3_utc = utc_datetime_from_local_hhmm(cls.reminder_3_time, tz)
    if r3_utc > now_utc:
        slots.append((3, r3_utc))

    for num, scheduled_at in slots:
        exists = db.query(Reminder).filter(
            Reminder.daily_wird_id == wird.id,
            Reminder.reminder_number == num,
        ).first()
        if not exists:
            db.add(Reminder(
                class_id=cls.id,
                daily_wird_id=wird.id,
                reminder_number=num,
                scheduled_at=scheduled_at,
                status=ReminderStatus.PENDING,
            ))
    db.commit()
