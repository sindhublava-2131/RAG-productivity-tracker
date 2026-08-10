from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics Dashboard"])

@router.get("", response_model=schemas.AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).all()
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    seven_days_ago = now - timedelta(days=7)
    start_of_month = datetime(now.year, now.month, 1)

    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == "COMPLETED"]
    pending_tasks = [t for t in tasks if t.status in ("PENDING", "IN_PROGRESS")]
    
    # 1. Daily completion (completed today)
    daily_completion = len([t for t in completed_tasks if t.completed_at and t.completed_at >= today_start])

    # 2. Weekly completion (completed in last 7 days)
    weekly_completion = len([t for t in completed_tasks if t.completed_at and t.completed_at >= seven_days_ago])

    # 3. Monthly progress (completed this month / total created this month %)
    month_created = [t for t in tasks if t.created_at >= start_of_month]
    month_completed = [t for t in completed_tasks if t.completed_at and t.completed_at >= start_of_month]
    monthly_progress_pct = (len(month_completed) / len(month_created) * 100.0) if month_created else 0.0

    # 4. Current streak (consecutive active days with at least 1 completed task)
    completed_dates = sorted(list(set(t.completed_at.date() for t in completed_tasks if t.completed_at)), reverse=True)
    streak = 0
    check_date = today_start.date()
    if completed_dates:
        if check_date in completed_dates or (check_date - timedelta(days=1)) in completed_dates:
            curr = check_date if check_date in completed_dates else (check_date - timedelta(days=1))
            while curr in completed_dates:
                streak += 1
                curr -= timedelta(days=1)

    # 5. Completion rate
    completion_rate_pct = (len(completed_tasks) / total_tasks * 100.0) if total_tasks > 0 else 0.0

    # 6. Overdue tasks
    overdue_tasks = len([
        t for t in tasks 
        if t.status != "COMPLETED" and t.due_date and t.due_date < now
    ])

    # 7. High-priority completion rate
    high_prio_total = [t for t in tasks if t.priority in ("HIGH", "URGENT")]
    high_prio_completed = [t for t in high_prio_total if t.status == "COMPLETED"]
    high_prio_pct = (len(high_prio_completed) / len(high_prio_total) * 100.0) if high_prio_total else 0.0

    # 8. Average completion time (minutes)
    completed_with_time = [t.actual_minutes for t in completed_tasks if t.actual_minutes > 0]
    avg_minutes = (sum(completed_with_time) / len(completed_with_time)) if completed_with_time else 0.0

    # 9. Completion by weekday (Mon-Sun)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    completion_by_weekday: Dict[str, int] = {day: 0 for day in weekdays}
    for t in completed_tasks:
        if t.completed_at:
            day_name = weekdays[t.completed_at.weekday()]
            completion_by_weekday[day_name] += 1

    # 10. Completion by hour (00 to 23)
    completion_by_hour: Dict[str, int] = {f"{h:02d}:00": 0 for h in range(24)}
    for t in completed_tasks:
        if t.completed_at:
            h_str = f"{t.completed_at.hour:02d}:00"
            completion_by_hour[h_str] += 1

    return schemas.AnalyticsResponse(
        daily_completion=daily_completion,
        weekly_completion=weekly_completion,
        monthly_progress_pct=round(monthly_progress_pct, 1),
        current_streak_days=streak,
        completion_rate_pct=round(completion_rate_pct, 1),
        total_tasks=total_tasks,
        completed_tasks=len(completed_tasks),
        pending_tasks=len(pending_tasks),
        overdue_tasks=overdue_tasks,
        high_priority_completion_pct=round(high_prio_pct, 1),
        avg_completion_minutes=round(avg_minutes, 1),
        completion_by_weekday=completion_by_weekday,
        completion_by_hour=completion_by_hour
    )
