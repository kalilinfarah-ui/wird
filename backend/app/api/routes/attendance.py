"""Attendance routes — real-time dashboard data"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.attendance_service import AttendanceService
from app.services.wird_service import WirdService
from app.models.student import Student
from app.models.attendance import Attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/{class_id}/today")
def get_today_attendance(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Today's full attendance list for a class."""
    svc = AttendanceService(db)
    return svc.get_today_attendance(class_id)


@router.get("/{class_id}/stats")
def get_stats(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = AttendanceService(db)
    return svc.get_stats_for_class(class_id)


@router.post("/{class_id}/manual-complete")
def manual_complete(
    class_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher manually marks a student as completed."""
    wird_svc = WirdService(db)
    att_svc = AttendanceService(db)

    today_wird = wird_svc.get_today_wird_by_class(class_id)
    if not today_wird:
        raise HTTPException(status_code=404, detail="لا يوجد ورد لليوم")

    att = att_svc.record(
        student_id=student_id,
        wird_id=str(today_wird.id),
        method="manual",
        note=f"تم التعيين يدوياً من {current_user.full_name}",
    )
    return {"status": "ok", "attendance_id": str(att.id)}


@router.get("/{class_id}/history")
def get_history(
    class_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Attendance calendar data for the last N days."""
    wird_svc = WirdService(db)
    wirds = wird_svc.get_history(class_id, days)

    result = []
    att_svc = AttendanceService(db)
    for wird in wirds:
        stats = att_svc.get_stats_for_class(class_id)
        result.append({
            "date": wird.wird_date.isoformat(),
            "wird_id": str(wird.id),
            "title": wird.title,
            "status": wird.status,
            "is_holiday": wird.is_holiday,
        })
    return result


@router.get("/{class_id}/student/{student_id}")
def get_student_history(
    class_id: str,
    student_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Individual student attendance history."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    since = date.today() - timedelta(days=days)
    wirds = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.completed_at >= since,
    ).order_by(Attendance.completed_at.desc()).all()

    return {
        "student": {
            "id": str(student.id),
            "full_name": student.full_name,
            "telegram_username": student.telegram_username,
            "current_streak": student.current_streak,
            "longest_streak": student.longest_streak,
            "total_completed": student.total_completed,
            "total_missed": student.total_missed,
            "completion_percentage": student.completion_percentage,
        },
        "history": [
            {
                "completed_at": a.completed_at.isoformat(),
                "method": a.completion_method,
            }
            for a in wirds
        ],
    }
