import enum
from datetime import datetime
from sqlalchemy import Column, String, Enum, Boolean, DateTime, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TEACHER = "teacher"
    ASSISTANT = "assistant"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TEACHER, nullable=False)

    # Telegram Login
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True)
    telegram_photo_url = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organizations = relationship("Organization", back_populates="owner")
    classes = relationship("ClassGroup", back_populates="teacher")

    def __repr__(self):
        return f"<User {self.full_name} ({self.role})>"
