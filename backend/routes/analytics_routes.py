from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
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
    """Compute the 11 productivity metrics using SQL aggregation.

    Only completed-task timestamps (needed for weekday/hour distributions and
    the streak) are materialized in Python; all counts are pushed to SQL.
    """
    now = _now_utc()
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    seven_days_ago = now - timedelta(days=7)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    base = db.query(models.Task).filter(models.Task.user_id == current_user.id)

    total_tasks = base.count()
    completed_tasks = base.filter(models.Task.status == "COMPLETED").count()
    pending_tasks = base.filter(
        models.Task.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()
    overdue_tasks = base.filter(
        models.Task.status != "COMPLETED", models.Task.due_date.isnot(None), models.Task.due_date < now
    ).count()

    daily_completion = base.filter(
        models.Task.status == "COMPLETED",
        models.Task.completed_at.isnot(None),
        models.Task.completed_at >= today_start,
    ).count()
    weekly_completion = base.filter(
        models.Task.status == "COMPLETED",
        models.Task.completed_at.isnot(None),
        models.Task.completed_at >= seven_days_ago,
    ).count()

    month_created = base.filter(models.Task.created_at >= start_of_month).count()
    month_completed = base.filter(
        models.Task.status == "COMPLETED",
        models.Task.completed_at.isnot(None),
        models.Task.completed_at >= start_of_month,
    ).count()
    monthly_progress_pct = (month_completed / month_created * 100.0) if month_created else 0.0

    completion_rate_pct = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

    high_prio_total = base.filter(models.Task.priority.in_(["HIGH", "URGENT"])).count()
    high_prio_completed = base.filter(
        models.Task.priority.in_(["HIGH", "URGENT"]),
        models.Task.status == "COMPLETED",
    ).count()
    high_prio_pct = (high_prio_completed / high_prio_total * 100.0) if high_prio_total else 0.0

    avg_minutes = (
        base.filter(
            models.Task.status == "COMPLETED", models.Task.actual_minutes > 0
        )
        .with_entities(func.avg(models.Task.actual_minutes))
        .scalar()
    )
    avg_minutes = round(float(avg_minutes or 0.0), 1)

    # Only completed timestamps are loaded for distributions + streak.
    completed_at_rows = (
        base.filter(
            models.Task.status == "COMPLETED",
            models.Task.completed_at.isnot(None),
        )
        .with_entities(models.Task.completed_at)
        .all()
    )
    completed_dts = [
        dt
        for (dt,) in completed_at_rows
        if (dt := _aware(dt)) is not None
    ]

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    completion_by_weekday: dict[str, int] = {day: 0 for day in weekdays}
    completion_by_hour: dict[str, int] = {f"{h:02d}:00": 0 for h in range(24)}
    for dt in completed_dts:
        completion_by_weekday[weekdays[dt.weekday()]] += 1
        completion_by_hour[f"{dt.hour:02d}:00"] += 1

    completed_dates = sorted({dt.date() for dt in completed_dts}, reverse=True)
    streak = 0
    check_date = today_start.date()
    if completed_dates:
        if check_date in completed_dates or (check_date - timedelta(days=1)) in completed_dates:
            curr = check_date if check_date in completed_dates else (check_date - timedelta(days=1))
            while curr in completed_dates:
                streak += 1
                curr -= timedelta(days=1)

    return schemas.AnalyticsResponse(
        daily_completion=daily_completion,
        weekly_completion=weekly_completion,
        monthly_progress_pct=round(monthly_progress_pct, 1),
        current_streak_days=streak,
        completion_rate_pct=round(completion_rate_pct, 1),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        high_priority_completion_pct=round(high_prio_pct, 1),
        avg_completion_minutes=avg_minutes,
        completion_by_weekday=completion_by_weekday,
        completion_by_hour=completion_by_hour,
    )
