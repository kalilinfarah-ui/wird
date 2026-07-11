from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class ClassGroup(Base):
    """A class/group that maps to a Telegram group or channel."""
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Telegram Group
    telegram_chat_id = Column(BigInteger, unique=True, nullable=True, index=True)
    telegram_chat_title = Column(String(255), nullable=True)
    telegram_chat_type = Column(String(50), nullable=True)  # group, supergroup, channel
    bot_token = Column(Text, nullable=True)  # each class can have its own bot

    # Settings
    wird_time = Column(String(10), default="07:00")  # HH:MM in teacher's timezone
    timezone = Column(String(50), default="Asia/Riyadh")
    reminder_1_hours = Column(String(10), default="2")   # hours after wird send
    reminder_2_hours = Column(String(10), default="6")
    reminder_3_time = Column(String(10), default="21:00")  # fixed time
    reminders_enabled = Column(Boolean, default=True)
    completion_keywords = Column(Text, default="تم,done,finished,✔,✅,قرأت,read")

    is_active = Column(Boolean, default=True)

    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = relationship("User", back_populates="classes")
    organization = relationship("Organization", back_populates="classes")
    students = relationship("Student", back_populates="class_group")
    daily_wirds = relationship("DailyWird", back_populates="class_group")
    reminders = relationship("Reminder", back_populates="class_group")
