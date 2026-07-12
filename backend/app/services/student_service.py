from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.student import Student
from app.models.class_group import ClassGroup


class StudentService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_telegram(self, telegram_id: int, chat_id: int) -> Optional[Student]:
        """Get student by telegram_id in a specific chat/class."""
        class_obj = self.db.query(ClassGroup).filter(
            ClassGroup.telegram_chat_id == chat_id
        ).first()
        if not class_obj:
            return None
        return self.db.query(Student).filter(
            and_(
                Student.telegram_id == telegram_id,
                Student.class_id == class_obj.id,
                Student.is_active == True,
            )
        ).first()

    def get_or_create_by_telegram(self, telegram_id: int, full_name: str,
                                   username: Optional[str], chat_id: int) -> Student:
        """Get existing or create new student when they interact in Telegram."""
        class_obj = self.db.query(ClassGroup).filter(
            ClassGroup.telegram_chat_id == chat_id
        ).first()
        if not class_obj:
            raise ValueError(f"No class linked to chat {chat_id}")

        student = self.db.query(Student).filter(
            and_(
                Student.telegram_id == telegram_id,
                Student.class_id == class_obj.id,
            )
        ).first()

        if not student:
            student = Student(
                telegram_id=telegram_id,
                full_name=full_name,
                telegram_username=username,
                class_id=class_obj.id,
                is_active=True,
                joined_at=datetime.utcnow(),
            )
            self.db.add(student)
            self.db.commit()
            self.db.refresh(student)
        else:
            # Sync name/username changes
            if student.full_name != full_name or student.telegram_username != username:
                student.full_name = full_name
                student.telegram_username = username
                student.updated_at = datetime.utcnow()
                self.db.commit()

        return student

    def mark_left(self, telegram_id: int, chat_id: int):
        student = self.get_by_telegram(telegram_id, chat_id)
        if student:
            student.is_active = False
            student.left_at = datetime.utcnow()
            self.db.commit()

    def get_class_students(self, class_id: str) -> list[Student]:
        return self.db.query(Student).filter(
            and_(Student.class_id == class_id, Student.is_active == True)
        ).order_by(Student.full_name).all()

    def update_stats(self, student_id: str, completed: bool):
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return
        if completed:
            student.total_completed += 1
            student.current_streak += 1
            if student.current_streak > student.longest_streak:
                student.longest_streak = student.current_streak
        else:
            student.total_missed += 1
            student.current_streak = 0
        student.updated_at = datetime.utcnow()
        self.db.commit()
