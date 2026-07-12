"""Reports — daily, weekly, monthly + export"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.daily_wird import DailyWird

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{class_id}/weekly")
def weekly_report(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    return _range_report(class_id, week_start, today, db)


@router.get("/{class_id}/monthly")
def monthly_report(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    month_start = today.replace(day=1)
    return _range_report(class_id, month_start, today, db)


@router.get("/{class_id}/range")
def range_report(
    class_id: str,
    start: date,
    end: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _range_report(class_id, start, end, db)


@router.get("/{class_id}/top-students")
def top_students(
    class_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    students = (
        db.query(Student)
        .filter(and_(Student.class_id == class_id, Student.is_active == True))
        .order_by(Student.total_completed.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "full_name": s.full_name,
            "telegram_username": s.telegram_username,
            "total_completed": s.total_completed,
            "current_streak": s.current_streak,
            "completion_percentage": s.completion_percentage,
        }
        for s in students
    ]


@router.get("/{class_id}/export/csv")
def export_csv(
    class_id: str,
    start: date = None,
    end: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import csv, io
    if not start:
        start = date.today().replace(day=1)
    if not end:
        end = date.today()

    students = db.query(Student).filter(
        and_(Student.class_id == class_id, Student.is_active == True)
    ).order_by(Student.full_name).all()

    wirds = db.query(DailyWird).filter(
        and_(
            DailyWird.class_id == class_id,
            DailyWird.wird_date >= start,
            DailyWird.wird_date <= end,
        )
    ).order_by(DailyWird.wird_date).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    header = ["الاسم", "المعرف", "إجمالي المكتمل", "إجمالي الغياب", "النسبة %", "السلسلة الحالية"]
    header += [w.wird_date.strftime("%d/%m") for w in wirds]
    writer.writerow(header)

    # Each student row
    for s in students:
        att_map = {
            str(a.daily_wird_id): a.completed_at.strftime("%H:%M")
            for a in db.query(Attendance).filter(Attendance.student_id == s.id).all()
        }
        row = [
            s.full_name,
            f"@{s.telegram_username}" if s.telegram_username else str(s.telegram_id),
            s.total_completed,
            s.total_missed,
            f"{s.completion_percentage}%",
            s.current_streak,
        ]
        for w in wirds:
            row.append(att_map.get(str(w.id), "—"))
        writer.writerow(row)

    content = output.getvalue().encode("utf-8-sig")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{start}_{end}.csv"},
    )


def _range_report(class_id: str, start: date, end: date, db: Session) -> dict:
    wirds = db.query(DailyWird).filter(
        and_(
            DailyWird.class_id == class_id,
            DailyWird.wird_date >= start,
            DailyWird.wird_date <= end,
        )
    ).all()

    total_students = db.query(func.count(Student.id)).filter(
        and_(Student.class_id == class_id, Student.is_active == True)
    ).scalar()

    daily = []
    total_completions = 0
    for w in wirds:
        count = db.query(func.count(Attendance.id)).filter(
            Attendance.daily_wird_id == w.id
        ).scalar()
        total_completions += count
        daily.append({
            "date": w.wird_date.isoformat(),
            "title": w.title,
            "completed": count,
            "total": total_students,
            "rate": round(count / total_students * 100, 1) if total_students else 0,
        })

    days = len(wirds) or 1
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total_students": total_students,
        "total_days": days,
        "average_completion_rate": round(total_completions / (days * total_students) * 100, 1) if total_students else 0,
        "daily": daily,
    }
