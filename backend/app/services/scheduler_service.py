"""
Scheduler — runs in background with APScheduler.
Handles: daily wird sending, 3-tier reminders, streak calculation.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from app.db.database import SessionLocal
from app.models.class_group import ClassGroup
from app.models.daily_wird import DailyWird, WirdStatus
from app.models.reminder import Reminder, ReminderStatus
from app.services.wird_service import WirdService
from app.services.attendance_service import AttendanceService
from app.telegram.bot import send_daily_wird

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def job_send_daily_wirds():
    """Run every minute — send any scheduled wirds whose time has come."""
    db = SessionLocal()
    try:
        wird_svc = WirdService(db)
        scheduled = wird_svc.get_scheduled_wirds()

        now = datetime.utcnow()
        for wird in scheduled:
            class_obj = wird.class_group
            if not class_obj.telegram_chat_id or not class_obj.bot_token:
                continue

            # Parse scheduled time (stored as HH:MM in class timezone)
            send_time_str = wird.scheduled_time or class_obj.wird_time
            hour, minute = map(int, send_time_str.split(":"))

            # Simple UTC check (TODO: timezone-aware with pytz)
            if now.hour == hour and now.minute == minute:
                try:
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
                    wird_svc.mark_sent(str(wird.id), msg_id)
                    await _schedule_reminders(db, wird, class_obj)
                    logger.info(f"Sent wird {wird.id} to chat {class_obj.telegram_chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send wird {wird.id}: {e}")
                    wird.status = WirdStatus.FAILED
                    db.commit()
    finally:
        db.close()


async def _schedule_reminders(db, wird: DailyWird, class_obj: ClassGroup):
    """Schedule 3 reminders for a wird after it's sent."""
    if not class_obj.reminders_enabled:
        return

    now = datetime.utcnow()
    reminder_times = [
        (1, now + timedelta(hours=int(class_obj.reminder_1_hours))),
        (2, now + timedelta(hours=int(class_obj.reminder_2_hours))),
    ]

    # Reminder 3: fixed time same day
    h, m = map(int, class_obj.reminder_3_time.split(":"))
    r3_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if r3_time > now:
        reminder_times.append((3, r3_time))

    for num, scheduled_at in reminder_times:
        reminder = Reminder(
            class_id=class_obj.id,
            daily_wird_id=wird.id,
            reminder_number=num,
            scheduled_at=scheduled_at,
            status=ReminderStatus.PENDING,
        )
        db.add(reminder)
    db.commit()


async def job_send_reminders():
    """Run every minute — send pending reminders whose time has come."""
    db = SessionLocal()
    try:
        att_svc = AttendanceService(db)
        now = datetime.utcnow()

        pending = db.query(Reminder).filter(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.scheduled_at <= now,
        ).all()

        for reminder in pending:
            class_obj = reminder.class_group
            if not class_obj.bot_token or not class_obj.telegram_chat_id:
                reminder.status = ReminderStatus.SKIPPED
                db.commit()
                continue

            try:
                pending_students = att_svc.get_pending_students(
                    str(class_obj.id), str(reminder.daily_wird_id)
                )
                if not pending_students:
                    reminder.status = ReminderStatus.SKIPPED
                    db.commit()
                    continue

                bot = Bot(token=class_obj.bot_token)
                names = "\n".join(f"• {s.full_name}" for s in pending_students[:20])
                count = len(pending_students)

                # Send to group
                await bot.send_message(
                    chat_id=class_obj.telegram_chat_id,
                    text=(
                        f"⏰ *تذكير — الورد اليومي*\n\n"
                        f"لم يُكمل *{count}* طالب الورد بعد.\n\n"
                        f"أكملوا ورد اليوم وسجلوا حضوركم 🌟"
                    ),
                    parse_mode="Markdown",
                )

                reminder.status = ReminderStatus.SENT
                reminder.sent_at = now
                reminder.recipients_count = count
                db.commit()

            except Exception as e:
                logger.error(f"Failed to send reminder {reminder.id}: {e}")
                reminder.status = ReminderStatus.FAILED
                db.commit()
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(job_send_daily_wirds, CronTrigger(minute="*"), id="send_wirds", replace_existing=True)
    scheduler.add_job(job_send_reminders, CronTrigger(minute="*"), id="send_reminders", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
