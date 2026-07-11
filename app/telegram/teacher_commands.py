"""
Teacher-only Telegram commands.
All handlers check that the sender is an authorized teacher for this chat.

Commands:
  /wird <text>          — Set today's wird content
  /report               — Today's attendance summary
  /report week          — Weekly table
  /remind               — Ping everyone who hasn't done it yet
  /summary              — Post the group summary now
  /settings             — Inline-button settings panel
  /addteacher           — Show instructions to authorize another teacher
  /id                   — Show this chat's Chat ID (useful during setup)
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    Bot,
)
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ContextTypes,
)
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.class_group import ClassGroup
from app.models.daily_wird import DailyWird, WirdStatus
from app.models.student import Student
from app.services.attendance_service import AttendanceService
from app.services.wird_service import WirdService
from app.services.student_service import StudentService

logger = logging.getLogger(__name__)


# ─── Auth guard ───────────────────────────────────────────────────────────────

def _get_class_for_teacher(chat_id: int, telegram_id: int, db: Session) -> Optional[ClassGroup]:
    """
    Return the ClassGroup for this chat IF the caller is the teacher or
    an authorized assistant (stored as comma-sep telegram IDs in teacher_telegram_ids).
    """
    cls = db.query(ClassGroup).filter(ClassGroup.telegram_chat_id == chat_id).first()
    if not cls:
        return None

    # The teacher who owns this class — look up via User.telegram_id
    from app.models.user import User
    teacher = db.query(User).filter(User.id == cls.teacher_id).first()
    if not teacher:
        return None

    # Build authorized set: teacher + any stored assistant IDs
    authorized: set[int] = set()
    if teacher.telegram_id:
        authorized.add(teacher.telegram_id)

    extra = (cls.description or "").split("TEACHERS:")[1].split("\n")[0].strip() \
        if "TEACHERS:" in (cls.description or "") else ""
    for tid in extra.split(","):
        try:
            authorized.add(int(tid.strip()))
        except ValueError:
            pass

    return cls if telegram_id in authorized else None


async def _not_authorized(update: Update):
    await update.message.reply_text("⛔ هذا الأمر مخصص للمعلمة فقط.")


# ─── /id ──────────────────────────────────────────────────────────────────────

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(
        f"🆔 *معلومات هذه المحادثة*\n\n"
        f"Chat ID: `{chat.id}`\n"
        f"النوع: {chat.type}\n"
        f"الاسم: {chat.title or chat.first_name}",
        parse_mode="Markdown"
    )


# ─── /wird <content> ──────────────────────────────────────────────────────────

async def cmd_set_wird(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return

        if not context.args:
            await update.message.reply_text(
                "📝 *كيفية تعيين ورد اليوم:*\n\n"
                "`/wird عنوان الورد`\n\n"
                "مثال:\n"
                "`/wird سورة الكهف — الآيات 1-10`",
                parse_mode="Markdown"
            )
            return

        title = " ".join(context.args)
        svc = WirdService(db)

        # Check if one already exists today
        existing = svc.get_today_wird_by_class(str(cls.id))
        if existing:
            existing.title = title
            existing.updated_at = datetime.utcnow()
            db.commit()
            await update.message.reply_text(f"✅ تم تحديث ورد اليوم:\n\n*{title}*", parse_mode="Markdown")
        else:
            svc.create_wird(class_id=str(cls.id), wird_date=date.today(), title=title)
            await update.message.reply_text(f"✅ تم حفظ ورد اليوم:\n\n*{title}*", parse_mode="Markdown")
    finally:
        db.close()


# ─── /report [week] ───────────────────────────────────────────────────────────

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return

        is_week = context.args and context.args[0].lower() in ("week", "أسبوع", "اسبوع")

        att_svc = AttendanceService(db)

        if is_week:
            await _send_weekly_report(update, cls, att_svc, db)
        else:
            await _send_daily_report(update, cls, att_svc, db)
    finally:
        db.close()


async def _send_daily_report(update, cls: ClassGroup, att_svc: AttendanceService, db: Session):
    records = att_svc.get_today_attendance(str(cls.id))
    if not records:
        await update.message.reply_text("📭 لا يوجد ورد لليوم بعد.")
        return

    completed = [r for r in records if r["completed"]]
    pending   = [r for r in records if not r["completed"]]
    total     = len(records)
    rate      = round(len(completed) / total * 100) if total else 0

    # Bar
    filled = round(rate / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    lines = [
        f"📊 *تقرير اليوم — {_ar_date(date.today())}*",
        f"",
        f"{bar}  {rate}%",
        f"✅ مكتمل: {len(completed)}/{total}",
        f"",
    ]

    if completed:
        lines.append("*أكملوا الورد:*")
        for r in completed:
            name = r["full_name"]
            time = r["completed_at"][11:16] if r["completed_at"] else ""
            lines.append(f"  ✅ {name}" + (f"  _{time}_" if time else ""))

    if pending:
        lines.append("")
        lines.append("*لم يكملوا بعد:*")
        for r in pending[:20]:
            lines.append(f"  ⏳ {r['full_name']}")
        if len(pending) > 20:
            lines.append(f"  _... و {len(pending)-20} آخرين_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _send_weekly_report(update, cls: ClassGroup, att_svc: AttendanceService, db: Session):
    today = date.today()
    lines = [f"📅 *التقرير الأسبوعي*\n"]

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        wird = db.query(DailyWird).filter(
            DailyWird.class_id == cls.id,
            DailyWird.wird_date == d,
        ).first()

        if not wird:
            lines.append(f"  {_ar_date(d)}: —")
            continue

        from sqlalchemy import func
        from app.models.attendance import Attendance
        from app.models.student import Student as StudentModel

        completed = db.query(func.count(Attendance.id)).filter(
            Attendance.daily_wird_id == wird.id
        ).scalar()
        total = db.query(func.count(StudentModel.id)).filter(
            StudentModel.class_id == cls.id,
            StudentModel.is_active == True,
        ).scalar()
        rate = round(completed / total * 100) if total else 0
        bar_short = "🟩" * round(rate/20) + "⬜" * (5 - round(rate/20))
        lines.append(f"  {_ar_date(d)}: {bar_short} {rate}% ({completed}/{total})")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /remind ──────────────────────────────────────────────────────────────────

async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return

        wird_svc = WirdService(db)
        att_svc = AttendanceService(db)

        today_wird = wird_svc.get_today_wird_by_class(str(cls.id))
        if not today_wird:
            await update.message.reply_text("❌ لا يوجد ورد لليوم.")
            return

        pending = att_svc.get_pending_students(str(cls.id), str(today_wird.id))
        if not pending:
            await update.message.reply_text("🎉 جميع الطلاب أكملوا الورد!")
            return

        names = "\n".join(f"• {s.full_name}" for s in pending)
        await update.message.reply_text(
            f"⏰ *تذكير يدوي*\n\n"
            f"لم يُكمل {len(pending)} طالب الورد بعد:\n\n"
            f"{names}\n\n"
            f"اضغط ✅ على رسالة الورد للتسجيل!",
            parse_mode="Markdown"
        )
    finally:
        db.close()


# ─── /summary — post the group completion recap now ───────────────────────────

async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return

        att_svc = AttendanceService(db)
        text = _build_summary_text(cls, att_svc, db)
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        db.close()


def _build_summary_text(cls: ClassGroup, att_svc: AttendanceService, db: Session) -> str:
    """Build the group summary message (reused by both /summary and the cron task)."""
    records = att_svc.get_today_attendance(str(cls.id))
    if not records:
        return "📭 لا يوجد ورد لليوم."

    completed = [r for r in records if r["completed"]]
    pending   = [r for r in records if not r["completed"]]
    total     = len(records)
    rate      = round(len(completed) / total * 100) if total else 0
    filled    = round(rate / 10)
    bar       = "🟩" * filled + "⬜" * (10 - filled)

    lines = [
        f"📖 *ملخص ورد اليوم — {_ar_date(date.today())}*",
        f"",
        f"{bar}  *{rate}%*",
        f"✅ أكمل: *{len(completed)}* من *{total}*",
        f"",
    ]

    if completed:
        lines.append("*من أكمل الورد:*")
        for r in completed:
            streak = r.get("current_streak", 0)
            streak_badge = f" 🔥{streak}" if streak >= 3 else ""
            lines.append(f"  ✅ {r['full_name']}{streak_badge}")

    if pending:
        lines.append("")
        lines.append(f"*لم يكملوا بعد ({len(pending)}):*")
        for r in pending[:15]:
            lines.append(f"  ⏳ {r['full_name']}")
        if len(pending) > 15:
            lines.append(f"  _... و {len(pending)-15} آخرين_")

    return "\n".join(lines)


# ─── /settings — inline button panel ─────────────────────────────────────────

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'🔔' if cls.reminders_enabled else '🔕'} التذكيرات: {'مفعّلة' if cls.reminders_enabled else 'معطّلة'}",
                    callback_data=f"setting:toggle_reminders:{cls.id}"
                )
            ],
            [
                InlineKeyboardButton("⏰ وقت الورد", callback_data=f"setting:show_time:{cls.id}"),
                InlineKeyboardButton("📋 الكلمات المقبولة", callback_data=f"setting:show_keywords:{cls.id}"),
            ],
            [
                InlineKeyboardButton("📊 إحصائيات الفصل", callback_data=f"setting:stats:{cls.id}"),
            ],
        ])

        await update.message.reply_text(
            f"⚙️ *إعدادات {cls.name}*\n\n"
            f"⏰ وقت الورد: `{cls.wird_time}`\n"
            f"🌍 المنطقة: `{cls.timezone}`\n"
            f"🔔 تذكير 1: بعد `{cls.reminder_1_hours}` ساعات\n"
            f"🔔 تذكير 2: بعد `{cls.reminder_2_hours}` ساعات\n"
            f"🔔 تذكير 3: الساعة `{cls.reminder_3_time}`",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    finally:
        db.close()


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    action = parts[1]
    class_id = parts[2]

    db = SessionLocal()
    try:
        cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not cls:
            return

        if action == "toggle_reminders":
            cls.reminders_enabled = not cls.reminders_enabled
            db.commit()
            status = "مفعّلة ✅" if cls.reminders_enabled else "معطّلة 🔕"
            await query.edit_message_text(f"✅ التذكيرات الآن {status}")

        elif action == "show_time":
            await query.edit_message_text(
                f"⏰ وقت إرسال الورد الحالي: *{cls.wird_time}*\n\n"
                f"لتغييره، أرسلي للمشرف أو عدّليه من لوحة التحكم.",
                parse_mode="Markdown"
            )

        elif action == "show_keywords":
            await query.edit_message_text(
                f"📋 *الكلمات المقبولة للتأكيد:*\n\n"
                f"`{cls.completion_keywords}`\n\n"
                f"عندما يرسل الطالب أي من هذه الكلمات يُسجَّل حضوره تلقائياً.",
                parse_mode="Markdown"
            )

        elif action == "stats":
            att_svc = AttendanceService(db)
            stats = att_svc.get_stats_for_class(class_id)
            await query.edit_message_text(
                f"📊 *إحصائيات اليوم — {cls.name}*\n\n"
                f"👥 إجمالي الطلاب: *{stats['total_students']}*\n"
                f"✅ أكملوا: *{stats['today_completed']}*\n"
                f"⏳ لم يكملوا: *{stats['today_pending']}*\n"
                f"📈 نسبة الإنجاز: *{stats['completion_rate']}%*",
                parse_mode="Markdown"
            )
    finally:
        db.close()


# ─── /addteacher ──────────────────────────────────────────────────────────────

async def cmd_addteacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        cls = _get_class_for_teacher(update.effective_chat.id, update.effective_user.id, db)
        if not cls:
            await _not_authorized(update)
            return
        await update.message.reply_text(
            "➕ *إضافة مشرف*\n\n"
            "لإضافة مشرف، أرسلي إلى لوحة التحكم وأضيفيه من إعدادات الفصل.\n\n"
            f"Telegram ID الخاص بك: `{update.effective_user.id}`\n"
            "أعطي المشرف هذا الأمر لمعرفة رقمه:\n`/myid`",
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Anyone can use this to find their own Telegram ID."""
    await update.message.reply_text(
        f"🆔 معرّفك في تيليغرام:\n\n`{update.effective_user.id}`\n\n"
        "أعطي هذا الرقم للمعلمة لإضافتك كمشرف.",
        parse_mode="Markdown"
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ar_date(d: date) -> str:
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
                 "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
    return f"{days_ar[d.weekday()]} {d.day} {months_ar[d.month-1]} {d.year}"


# ─── Register handlers ────────────────────────────────────────────────────────

def register_teacher_handlers(app):
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("wird", cmd_set_wird))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("addteacher", cmd_addteacher))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern=r"^setting:"))
