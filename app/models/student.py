from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Telegram Info (auto-synced)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    telegram_username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    photo_url = Column(Text, nullable=True)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)

    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    # Stats (denormalized for performance)
    total_completed = Column(Integer, default=0)
    total_missed = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_group = relationship("ClassGroup", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")
    streaks = relationship("Streak", back_populates="student")

    @property
    def completion_percentage(self) -> float:
        total = self.total_completed + self.total_missed
        if total == 0:
            return 0.0
        return round((self.total_completed / total) * 100, 1)

    def __repr__(self):
        return f"<Student {self.full_name} ({self.telegram_username})>"
