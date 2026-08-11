from __future__ import annotations

from datetime import UTC, datetime, timedelta

import models


def test_analytics_empty_user(client, auth_headers):
    response = client.get("/api/analytics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    assert data["pending_tasks"] == 0
    assert data["overdue_tasks"] == 0
    assert data["completion_rate_pct"] == 0.0
    assert data["monthly_progress_pct"] == 0.0
    assert data["avg_completion_minutes"] == 0.0
    assert len(data["completion_by_weekday"]) == 7
    assert len(data["completion_by_hour"]) == 24


def test_analytics_normal_and_completed_tasks(client, auth_headers, db_session, test_user):
    now = datetime.now(UTC)

    t1 = models.Task(
        user_id=test_user.id,
        title="Pending High Priority Task",
        priority="HIGH",
        status="PENDING",
        due_date=now + timedelta(days=2),
    )
    t2 = models.Task(
        user_id=test_user.id,
        title="Completed Urgent Task",
        priority="URGENT",
        status="COMPLETED",
        completed_at=now - timedelta(hours=1),
        actual_minutes=45,
    )
    t3 = models.Task(
        user_id=test_user.id,
        title="Overdue Low Priority Task",
        priority="LOW",
        status="PENDING",
        due_date=now - timedelta(days=1),
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    response = client.get("/api/analytics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_tasks"] == 3
    assert data["completed_tasks"] == 1
    assert data["pending_tasks"] == 2
    assert data["overdue_tasks"] == 1
    assert data["avg_completion_minutes"] == 45.0
    assert data["high_priority_completion_pct"] == 50.0  # 1 of 2 (HIGH/URGENT) completed
