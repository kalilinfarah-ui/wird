from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.daily_wird import DailyWird, WirdStatus
from app.models.class_group import ClassGroup


class WirdService:
    def __init__(self, db: Session):
        self.db = db

    def get_today_wird_by_chat(self, chat_id: int) -> Optional[DailyWird]:
        from app.utils.timezone import local_date as tz_local_date
        class_obj = self.db.query(ClassGroup).filter(
            ClassGroup.telegram_chat_id == chat_id
        ).first()
        if not class_obj:
            return None
        # Use the class's local date so e.g. Algeria stays in sync at midnight
        today = tz_local_date(class_obj.timezone or "UTC")
        return self.db.query(DailyWird).filter(
            and_(
                DailyWird.class_id == class_obj.id,
                DailyWird.wird_date == today,
            )
        ).first()

    def get_today_wird_by_class(
        self, class_id: str, today: Optional[date] = None
    ) -> Optional[DailyWird]:
        """Return the wird for the given date (defaults to UTC today if omitted).
        Pass a timezone-aware local date when calling from cron tasks."""
        today = today or date.today()
        return self.db.query(DailyWird).filter(
            and_(
                DailyWird.class_id == class_id,
                DailyWird.wird_date == today,
            )
        ).first()

    def create_wird(self, class_id: str, wird_date: date, title: str,
                    content: Optional[str] = None, file_url: Optional[str] = None,
                    file_type: Optional[str] = None, motivational: Optional[str] = None,
                    wird_type: str = "quran") -> DailyWird:
        wird = DailyWird(
            class_id=class_id,
            wird_date=wird_date,
            title=title,
            content=content,
            file_url=file_url,
            file_type=file_type,
            motivational_message=motivational,
            wird_type=wird_type,
            status=WirdStatus.SCHEDULED,
        )
        self.db.add(wird)
        self.db.commit()
        self.db.refresh(wird)
        return wird

    def mark_sent(self, wird_id: str, message_id: int):
        wird = self.db.query(DailyWird).filter(DailyWird.id == wird_id).first()
        if wird:
            wird.status = WirdStatus.SENT
            wird.telegram_message_id = message_id
            wird.sent_at = datetime.utcnow()
            self.db.commit()

    def get_scheduled_wirds(self) -> List[DailyWird]:
        """Wirds scheduled for today that haven't been sent yet."""
        return self.db.query(DailyWird).filter(
            and_(
                DailyWird.wird_date == date.today(),
                DailyWird.status == WirdStatus.SCHEDULED,
                DailyWird.is_holiday == False,
            )
        ).all()

    def get_history(self, class_id: str, days: int = 30) -> List[DailyWird]:
        since = date.today() - timedelta(days=days)
        return self.db.query(DailyWird).filter(
            and_(
                DailyWird.class_id == class_id,
                DailyWird.wird_date >= since,
            )
        ).order_by(DailyWird.wird_date.desc()).all()
