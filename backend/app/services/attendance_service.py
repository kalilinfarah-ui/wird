from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.attendance import Attendance, CompletionMethod
from app.models.student import Student
from app.models.daily_wird import DailyWird
from app.services.student_service import StudentService


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db

    def is_completed(self, student_id: str, wird_id: str) -> bool:
        return self.db.query(Attendance).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.daily_wird_id == wird_id,
            )
        ).first() is not None

    def record(self, student_id: str, wird_id: str, method: str = "button",
               note: Optional[str] = None) -> Attendance:
        """Record a completion. Idempotent — safe to call multiple times."""
        existing = self.db.query(Attendance).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.daily_wird_id == wird_id,
            )
        ).first()
        if existing:
            return existing

        # Get class_id from wird
        wird = self.db.query(DailyWird).filter(DailyWird.id == wird_id).first()
        if not wird:
            raise ValueError(f"Wird {wird_id} not found")

        attendance = Attendance(
            student_id=student_id,
            daily_wird_id=wird_id,
            class_id=wird.class_id,
            completed_at=datetime.utcnow(),
            completion_method=CompletionMethod(method),
            note=note,
        )
        self.db.add(attendance)

        # Update student stats
        student_svc = StudentService(self.db)
        student_svc.update_stats(student_id, completed=True)

        self.db.commit()
        self.db.refresh(attendance)
        return attendance

    def get_today_attendance(self, class_id: str) -> List[dict]:
        """Return attendance summary for today."""
        today = date.today()
        wird = self.db.query(DailyWird).filter(
            and_(
                DailyWird.class_id == class_id,
                DailyWird.wird_date == today,
            )
        ).first()

        if not wird:
            return []

        students = self.db.query(Student).filter(
            and_(Student.class_id == class_id, Student.is_active == True)
        ).all()

        completed_ids = {
            str(a.student_id)
            for a in self.db.query(Attendance).filter(
                Attendance.daily_wird_id == wird.id
            ).all()
        }

        result = []
        for s in students:
            completed = str(s.id) in completed_ids
            att = None
            if completed:
                att = self.db.query(Attendance).filter(
                    and_(
                        Attendance.student_id == s.id,
                        Attendance.daily_wird_id == wird.id,
                    )
                ).first()
            result.append({
                "student_id": str(s.id),
                "full_name": s.full_name,
                "telegram_username": s.telegram_username,
                "telegram_id": s.telegram_id,
                "completed": completed,
                "completed_at": att.completed_at.isoformat() if att else None,
                "method": att.completion_method if att else None,
                "current_streak": s.current_streak,
                "completion_percentage": s.completion_percentage,
            })
        return sorted(result, key=lambda x: (not x["completed"], x["full_name"]))

    def get_pending_students(self, class_id: str, wird_id: str) -> List[Student]:
        """Students who haven't completed yet — for reminders."""
        completed_ids = [
            a.student_id for a in
            self.db.query(Attendance.student_id).filter(
                Attendance.daily_wird_id == wird_id
            ).all()
        ]
        return self.db.query(Student).filter(
            and_(
                Student.class_id == class_id,
                Student.is_active == True,
                ~Student.id.in_(completed_ids),
            )
        ).all()

    def get_stats_for_class(self, class_id: str) -> dict:
        today = date.today()
        total_students = self.db.query(func.count(Student.id)).filter(
            and_(Student.class_id == class_id, Student.is_active == True)
        ).scalar()

        today_wird = self.db.query(DailyWird).filter(
            and_(DailyWird.class_id == class_id, DailyWird.wird_date == today)
        ).first()

        today_completed = 0
        if today_wird:
            today_completed = self.db.query(func.count(Attendance.id)).filter(
                Attendance.daily_wird_id == today_wird.id
            ).scalar()

        return {
            "total_students": total_students,
            "today_completed": today_completed,
            "today_pending": max(0, total_students - today_completed),
            "completion_rate": round((today_completed / total_students * 100), 1) if total_students else 0,
        }
