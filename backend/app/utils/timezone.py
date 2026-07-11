"""
Timezone utilities — convert UTC <-> local time for any class timezone.

Supported timezones include (not exhaustive):
  Africa/Algiers   UTC+1  (Algeria, Tunisia)
  Asia/Riyadh      UTC+3  (Saudi Arabia)
  Africa/Cairo     UTC+2  (Egypt)
  Asia/Dubai       UTC+4  (UAE)
  Africa/Casablanca UTC+1 (Morocco)
  Africa/Tunis     UTC+1  (Tunisia)
  Asia/Amman       UTC+3  (Jordan)
  Asia/Baghdad     UTC+3  (Iraq)
  Asia/Beirut      UTC+3  (Lebanon)
  Europe/London    UTC+0/1

All timezone strings must be valid pytz names.
"""
from datetime import datetime
from typing import Optional
import pytz


def utc_now_in_tz(timezone_str: str) -> datetime:
    """Return current UTC time converted to a local timezone-aware datetime."""
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone("UTC")
    return datetime.now(tz=pytz.utc).astimezone(tz)


def local_hhmm(timezone_str: str) -> str:
    """Return current local time as 'HH:MM' string in the given timezone."""
    return utc_now_in_tz(timezone_str).strftime("%H:%M")


def local_date(timezone_str: str):
    """Return today's local date in the given timezone."""
    return utc_now_in_tz(timezone_str).date()


def is_wird_time(scheduled_hhmm: str, timezone_str: str, tolerance_minutes: int = 1) -> bool:
    """
    Check whether right now (in the class's local timezone) matches the
    scheduled HH:MM, within ±tolerance_minutes.

    Example:
      Algeria  (Africa/Algiers, UTC+1):  scheduled=07:00
      When UTC is 06:00 → local is 07:00 → returns True ✅
      When UTC is 07:00 → local is 08:00 → returns False ✅
    """
    now_local = utc_now_in_tz(timezone_str)
    now_minutes = now_local.hour * 60 + now_local.minute

    try:
        sh, sm = map(int, scheduled_hhmm.split(":"))
    except (ValueError, AttributeError):
        return False

    scheduled_minutes = sh * 60 + sm
    return abs(now_minutes - scheduled_minutes) <= tolerance_minutes


def utc_datetime_from_local_hhmm(hhmm: str, timezone_str: str) -> datetime:
    """
    Given a local HH:MM string, return a UTC-aware datetime for TODAY in
    that timezone.  Useful for scheduling reminders at a fixed local time.
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc

    h, m = map(int, hhmm.split(":"))
    today_local = datetime.now(tz=tz).replace(hour=h, minute=m, second=0, microsecond=0)
    return today_local.astimezone(pytz.utc)


# Ordered list for the UI dropdown — add more as needed
SUPPORTED_TIMEZONES = [
    ("Africa/Algiers",    "الجزائر، تونس (UTC+1)"),
    ("Asia/Riyadh",       "السعودية، الكويت، قطر (UTC+3)"),
    ("Africa/Cairo",      "مصر (UTC+2)"),
    ("Asia/Dubai",        "الإمارات، عُمان (UTC+4)"),
    ("Africa/Casablanca", "المغرب (UTC+1)"),
    ("Asia/Amman",        "الأردن (UTC+3)"),
    ("Asia/Beirut",       "لبنان (UTC+3)"),
    ("Asia/Baghdad",      "العراق (UTC+3)"),
    ("Asia/Kuwait",       "الكويت (UTC+3)"),
    ("Africa/Tripoli",    "ليبيا (UTC+2)"),
    ("Asia/Aden",         "اليمن (UTC+3)"),
    ("Asia/Muscat",       "عُمان (UTC+4)"),
    ("Europe/London",     "المملكة المتحدة (UTC+0/1)"),
    ("Europe/Paris",      "أوروبا الوسطى (UTC+1/2)"),
    ("UTC",               "UTC (توقيت عالمي)"),
]
