import enum
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Date, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class WirdType(str, enum.Enum):
    QURAN = "quran"
    ADHKAR = "adhkar"
    HADITH = "hadith"
    MIXED = "mixed"


class WirdStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"


class DailyWird(Base):
    __tablename__ = "daily_wirds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    wird_date = Column(Date, nullable=False, index=True)
    wird_type = Column(Enum(WirdType), default=WirdType.QURAN)

    # Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)           # text content
    file_url = Column(Text, nullable=True)          # PDF, image, audio, video
    file_type = Column(String(50), nullable=True)   # pdf, image, audio, video
    motivational_message = Column(Text, nullable=True)

    # Telegram message tracking
    telegram_message_id = Column(BigInteger, nullable=True)
    status = Column(Enum(WirdStatus), default=WirdStatus.SCHEDULED)
    sent_at = Column(DateTime, nullable=True)

    # Scheduling
    scheduled_time = Column(String(10), nullable=True)  # override class default
    is_holiday = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_group = relationship("ClassGroup", back_populates="daily_wirds")
    attendances = relationship("Attendance", back_populates="daily_wird")
    reminders = relationship("Reminder", back_populates="daily_wird")

    def __repr__(self):
        return f"<DailyWird {self.wird_date} - {self.title[:30]}>"
