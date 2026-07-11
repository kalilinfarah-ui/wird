import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class CompletionMethod(str, enum.Enum):
    BUTTON = "button"           # clicked inline button
    KEYWORD = "keyword"         # replied with keyword
    REACTION = "reaction"       # reacted to message
    MANUAL = "manual"           # teacher marked manually


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    daily_wird_id = Column(UUID(as_uuid=True), ForeignKey("daily_wirds.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)

    completed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completion_method = Column(Enum(CompletionMethod), default=CompletionMethod.BUTTON)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="attendances")
    daily_wird = relationship("DailyWird", back_populates="attendances")

    def __repr__(self):
        return f"<Attendance student={self.student_id} wird={self.daily_wird_id}>"
