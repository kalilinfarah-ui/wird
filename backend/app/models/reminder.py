import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    daily_wird_id = Column(UUID(as_uuid=True), ForeignKey("daily_wirds.id"), nullable=False)

    reminder_number = Column(Integer, nullable=False)  # 1, 2, 3
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING)
    recipients_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    class_group = relationship("ClassGroup", back_populates="reminders")
    daily_wird = relationship("DailyWird", back_populates="reminders")
