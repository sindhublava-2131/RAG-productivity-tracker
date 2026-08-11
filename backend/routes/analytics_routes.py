from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics Dashboard"])


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite strips tzinfo from DateTime(timezone=True); re-attach UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


@router.get("", response_model=schemas.AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).all()
    now = _now_utc()
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    seven_days_ago = now - timedelta(days=7)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == "COMPLETED"]
    pending_tasks = [t for t in tasks if t.status in ("PENDING", "IN_PROGRESS")]

    daily_completion = len(
        [
            t
            for t in completed_tasks
            if (_daily := _aware(t.completed_at)) is not None and _daily >= today_start
        ]
    )
    weekly_completion = len(
        [
            t
            for t in completed_tasks
            if (_weekly := _aware(t.completed_at)) is not None and _weekly >= seven_days_ago
        ]
    )

    month_created = [t for t in tasks if (_created := _aware(t.created_at)) is not None and _created >= start_of_month]
    month_completed = [
        t
        for t in completed_tasks
        if (_completed := _aware(t.completed_at)) is not None and _completed >= start_of_month
    ]
    monthly_progress_pct = (len(month_completed) / len(month_created) * 100.0) if month_created else 0.0

    completed_dates = sorted(
        {
            aware.date()
            for t in completed_tasks
            if (aware := _aware(t.completed_at)) is not None
        },
        reverse=True,
    )
    streak = 0
    check_date = today_start.date()
    if completed_dates:
        if check_date in completed_dates or (check_date - timedelta(days=1)) in completed_dates:
            curr = check_date if check_date in completed_dates else (check_date - timedelta(days=1))
            while curr in completed_dates:
                streak += 1
                curr -= timedelta(days=1)

    completion_rate_pct = (len(completed_tasks) / total_tasks * 100.0) if total_tasks > 0 else 0.0

    overdue_tasks = len(
        [
            t
            for t in tasks
            if t.status != "COMPLETED"
            and (_due := _aware(t.due_date)) is not None
            and _due < now
        ]
    )

    high_prio_total = [t for t in tasks if t.priority in ("HIGH", "URGENT")]
    high_prio_completed = [t for t in high_prio_total if t.status == "COMPLETED"]
    high_prio_pct = (len(high_prio_completed) / len(high_prio_total) * 100.0) if high_prio_total else 0.0

    completed_with_time = [t.actual_minutes for t in completed_tasks if t.actual_minutes > 0]
    avg_minutes = (sum(completed_with_time) / len(completed_with_time)) if completed_with_time else 0.0

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    completion_by_weekday: dict[str, int] = {day: 0 for day in weekdays}
    for t in completed_tasks:
        if t.completed_at:
            completion_by_weekday[weekdays[t.completed_at.weekday()]] += 1

    completion_by_hour: dict[str, int] = {f"{h:02d}:00": 0 for h in range(24)}
    for t in completed_tasks:
        if t.completed_at:
            completion_by_hour[f"{t.completed_at.hour:02d}:00"] += 1

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
        completion_by_hour=completion_by_hour,
    )
