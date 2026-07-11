"""
Core Telegram Bot — Webhook Handler
Handles: button callbacks, keyword messages, /commands, member events
"""
import logging
from datetime import datetime, date
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.services.attendance_service import AttendanceService
from app.services.student_service import StudentService
from app.services.wird_service import WirdService

logger = logging.getLogger(__name__)

# ─── Callback Data Prefixes ──────────────────────────────────────────────────
COMPLETE_CB = "complete"       # complete:{wird_id}
ALREADY_CB = "already"         # already:{wird_id}


# ─── Helper ──────────────────────────────────────────────────────────────────

def get_db() -> Session:
    return SessionLocal()


def build_wird_keyboard(wird_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ أكملت ورد اليوم", callback_data=f"{COMPLETE_CB}:{wird_id}")]
    ])


# ─── Send Daily Wird ─────────────────────────────────────────────────────────

async def send_daily_wird(bot: Bot, chat_id: int, wird_id: str, title: str,
                           content: Optional[str], file_url: Optional[str],
                           file_type: Optional[str], motivational: Optional[str]) -> int:
    """Send wird to a Telegram group. Returns message_id."""
    keyboard = build_wird_keyboard(wird_id)

    text = f"📖 *ورد اليوم*\n\n*{title}*"
    if content:
        text += f"\n\n{content}"
    if motivational:
        text += f"\n\n_{motivational}_"

    msg = None
    if file_url and file_type:
        if file_type == "image":
            msg = await bot.send_photo(chat_id=chat_id, photo=file_url,
                                        caption=text, parse_mode="Markdown",
                                        reply_markup=keyboard)
        elif file_type == "pdf":
            msg = await bot.send_document(chat_id=chat_id, document=file_url,
                                           caption=text, parse_mode="Markdown",
                                           reply_markup=keyboard)
        elif file_type == "audio":
            msg = await bot.send_audio(chat_id=chat_id, audio=file_url,
                                        caption=text, parse_mode="Markdown",
                                        reply_markup=keyboard)
        elif file_type == "video":
            msg = await bot.send_video(chat_id=chat_id, video=file_url,
                                        caption=text, parse_mode="Markdown",
                                        reply_markup=keyboard)

    if not msg:
        msg = await bot.send_message(chat_id=chat_id, text=text,
                                      parse_mode="Markdown", reply_markup=keyboard)
    return msg.message_id


# ─── Callback: Button Click ───────────────────────────────────────────────────

async def handle_complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # "complete:{wird_id}"
    wird_id = data.split(":")[1]

    user = query.from_user
    chat_id = query.message.chat_id

    db = get_db()
    try:
        student_svc = StudentService(db)
        attendance_svc = AttendanceService(db)

        # Find or create student
        student = student_svc.get_or_create_by_telegram(
            telegram_id=user.id,
            full_name=user.full_name or user.first_name,
            username=user.username,
            chat_id=chat_id,
        )

        # Check already completed
        already = attendance_svc.is_completed(student.id, wird_id)
        if already:
            await query.answer("✅ لقد أكملت ورد اليوم مسبقاً!", show_alert=True)
            return

        # Record attendance
        attendance_svc.record(
            student_id=student.id,
            wird_id=wird_id,
            method="button",
        )

        # Update button to show completion
        completed_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"✅ تم الإكمال في {datetime.now().strftime('%H:%M')}",
                callback_data=f"{ALREADY_CB}:{wird_id}"
            )]
        ])
        await query.edit_message_reply_markup(reply_markup=completed_keyboard)

    except Exception as e:
        logger.error(f"Error recording attendance: {e}")
        await query.answer("حدث خطأ، حاول مجدداً", show_alert=True)
    finally:
        db.close()


async def handle_already_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ لقد أكملت ورد اليوم!", show_alert=True)


# ─── Keyword Detection ────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg_text = update.message.text.strip().lower()
    chat_id = update.message.chat_id
    user = update.message.from_user

    db = get_db()
    try:
        wird_svc = WirdService(db)
        student_svc = StudentService(db)
        attendance_svc = AttendanceService(db)

        # Get today's wird for this chat
        today_wird = wird_svc.get_today_wird_by_chat(chat_id)
        if not today_wird:
            return

        # Get class keywords
        keywords = [k.strip().lower() for k in today_wird.class_group.completion_keywords.split(",")]
        if msg_text not in keywords:
            return

        student = student_svc.get_or_create_by_telegram(
            telegram_id=user.id,
            full_name=user.full_name or user.first_name,
            username=user.username,
            chat_id=chat_id,
        )

        if attendance_svc.is_completed(student.id, str(today_wird.id)):
            return  # silent — already done

        attendance_svc.record(
            student_id=student.id,
            wird_id=str(today_wird.id),
            method="keyword",
        )
        # React to message
        await update.message.set_reaction("👍")

    except Exception as e:
        logger.error(f"Error handling keyword: {e}")
    finally:
        db.close()


# ─── New Member Sync ──────────────────────────────────────────────────────────

async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return

    chat_id = result.chat.id
    member = result.new_chat_member
    user = member.user

    db = get_db()
    try:
        student_svc = StudentService(db)
        if member.status in ("member", "administrator"):
            student_svc.get_or_create_by_telegram(
                telegram_id=user.id,
                full_name=user.full_name or user.first_name,
                username=user.username,
                chat_id=chat_id,
            )
        elif member.status in ("left", "kicked", "banned"):
            student_svc.mark_left(telegram_id=user.id, chat_id=chat_id)
    except Exception as e:
        logger.error(f"Error syncing member: {e}")
    finally:
        db.close()


# ─── Commands ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 *مرحباً بك في نظام الورد اليومي*\n\n"
        "سيتم إرسال ورد اليوم تلقائياً في الوقت المحدد.\n"
        "اضغط على زر ✅ بعد الانتهاء لتسجيل حضورك.\n\n"
        "الأوامر المتاحة:\n"
        "/today — ورد اليوم\n"
        "/myprogress — تقدمي\n"
        "/streak — سلسلتي",
        parse_mode="Markdown"
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    db = get_db()
    try:
        wird_svc = WirdService(db)
        today_wird = wird_svc.get_today_wird_by_chat(chat_id)
        if not today_wird:
            await update.message.reply_text("📭 لا يوجد ورد لليوم.")
            return
        keyboard = build_wird_keyboard(str(today_wird.id))
        await update.message.reply_text(
            f"📖 *ورد اليوم*\n\n*{today_wird.title}*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    finally:
        db.close()


async def cmd_myprogress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    db = get_db()
    try:
        student_svc = StudentService(db)
        student = student_svc.get_by_telegram(user.id, chat_id)
        if not student:
            await update.message.reply_text("لم تُسجَّل بعد. ابدأ بالضغط على زر الورد.")
            return
        await update.message.reply_text(
            f"📊 *تقدمي*\n\n"
            f"✅ مكتمل: {student.total_completed}\n"
            f"❌ غائب: {student.total_missed}\n"
            f"🔥 السلسلة الحالية: {student.current_streak} يوم\n"
            f"🏆 أطول سلسلة: {student.longest_streak} يوم\n"
            f"📈 نسبة الإنجاز: {student.completion_percentage}%",
            parse_mode="Markdown"
        )
    finally:
        db.close()


async def cmd_streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    db = get_db()
    try:
        student_svc = StudentService(db)
        student = student_svc.get_by_telegram(user.id, chat_id)
        if not student:
            await update.message.reply_text("لم تُسجَّل بعد.")
            return
        streaks = "🔥" * min(student.current_streak, 30)
        await update.message.reply_text(
            f"🔥 *سلسلتك الحالية: {student.current_streak} يوم*\n\n{streaks}",
            parse_mode="Markdown"
        )
    finally:
        db.close()


# ─── Application Builder ──────────────────────────────────────────────────────

def create_application(token: str) -> Application:
    from app.telegram.teacher_commands import register_teacher_handlers

    app = Application.builder().token(token).build()

    # Student commands (public)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("myprogress", cmd_myprogress))
    app.add_handler(CommandHandler("streak", cmd_streak))

    # Completion callbacks
    app.add_handler(CallbackQueryHandler(handle_complete_callback, pattern=f"^{COMPLETE_CB}:"))
    app.add_handler(CallbackQueryHandler(handle_already_callback, pattern=f"^{ALREADY_CB}:"))

    # Teacher commands (restricted by Telegram ID inside each handler)
    register_teacher_handlers(app)

    # Keyword detection & member sync
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(handle_chat_member))

    return app
