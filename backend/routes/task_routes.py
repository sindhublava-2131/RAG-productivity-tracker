from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db
from services.rag.memory import MemoryIngestionError, format_task_memory
from services.rag.service import get_rag_service

logger = logging.getLogger("cozy.routes.tasks")

router = APIRouter(prefix="/api/tasks", tags=["Task Management"])


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _persist_memory(
    user_id: int,
    *,
    task_id: int | None,
    action: str,
    content: str,
    task: models.Task | None = None,
) -> None:
    """Persist a RAG memory; surface failures explicitly without failing the task op."""
    try:
        rag = get_rag_service()
        rag.store_memory_from_task(
            user_id=user_id,
            task_id=task_id,
            action=action,
            content=content,
            task_title=task.title if task else None,
            priority=task.priority if task else None,
            status=task.status if task else None,
            due_date=task.due_date if task else None,
            completed_at=task.completed_at if task else None,
            estimated_minutes=task.estimated_minutes if task else None,
            actual_minutes=task.actual_minutes if task else None,
        )
    except MemoryIngestionError as exc:
        logger.error("Memory persistence failed for task %s: %s", task_id, exc)


@router.get("", response_model=list[schemas.TaskResponse])
def get_tasks(
    status_filter: str | None = Query(default=None),
    priority_filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)
    if status_filter:
        query = query.filter(models.Task.status == status_filter.upper())
    if priority_filter:
        query = query.filter(models.Task.priority == priority_filter.upper())

    tasks = query.order_by(models.Task.created_at.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    new_task = models.Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority.value,
        status=task_in.status.value,
        due_date=task_in.due_date,
        estimated_minutes=task_in.estimated_minutes,
        actual_minutes=task_in.actual_minutes,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    mem_text = format_task_memory(
        "CREATE",
        {
            "title": new_task.title,
            "priority": new_task.priority,
            "estimated_minutes": new_task.estimated_minutes,
            "due_date": new_task.due_date.strftime("%Y-%m-%d") if new_task.due_date else None,
        },
    )
    _persist_memory(current_user.id, task_id=new_task.id, action="CREATE", content=mem_text, task=new_task)

    return new_task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    prev_due = task.due_date
    prev_status = task.status

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "priority" and value:
            setattr(task, field, value.value)
        elif field == "status" and value:
            setattr(task, field, value.value)
        else:
            setattr(task, field, value)

    if task.status == "COMPLETED" and not task.completed_at:
        task.completed_at = _utcnow()

    db.commit()
    db.refresh(task)

    if prev_due and task.due_date and task.due_date > prev_due:
        mem_text = format_task_memory(
            "DELAY",
            {
                "title": task.title,
                "priority": task.priority,
                "delay_note": f"due date moved from {prev_due.strftime('%Y-%m-%d')} to {task.due_date.strftime('%Y-%m-%d')}",
            },
        )
        _persist_memory(current_user.id, task_id=task.id, action="DELAY", content=mem_text, task=task)
    elif task.status == "COMPLETED" and prev_status != "COMPLETED":
        mem_text = format_task_memory(
            "COMPLETE",
            {
                "title": task.title,
                "estimated_minutes": task.estimated_minutes,
                "actual_minutes": task.actual_minutes,
            },
        )
        _persist_memory(current_user.id, task_id=task.id, action="COMPLETE", content=mem_text, task=task)
    else:
        mem_text = format_task_memory(
            "UPDATE",
            {
                "title": task.title,
                "status": task.status,
                "actual_minutes": task.actual_minutes,
            },
        )
        _persist_memory(current_user.id, task_id=task.id, action="UPDATE", content=mem_text, task=task)

    return task


@router.patch("/{task_id}/complete", response_model=schemas.TaskResponse)
@router.put("/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(
    task_id: int,
    actual_minutes: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "COMPLETED"
    task.completed_at = _utcnow()
    if actual_minutes is not None:
        task.actual_minutes = actual_minutes

    db.commit()
    db.refresh(task)

    mem_text = format_task_memory(
        "COMPLETE",
        {
            "title": task.title,
            "estimated_minutes": task.estimated_minutes,
            "actual_minutes": task.actual_minutes,
        },
    )
    _persist_memory(current_user.id, task_id=task.id, action="COMPLETE", content=mem_text, task=task)

    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    task_id_value = task.id
    db.delete(task)
    db.commit()

    mem_text = f"Deleted task '{title}' on {_utcnow().strftime('%Y-%m-%d %H:%M')}."
    _persist_memory(current_user.id, task_id=task_id_value, action="DELETE", content=mem_text)

    return {"detail": "Task successfully deleted"}
