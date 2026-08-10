from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas
import auth
from database import get_db
import rag_service

router = APIRouter(prefix="/api/tasks", tags=["Task Management"])

@router.get("", response_model=List[schemas.TaskResponse])
def get_tasks(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)
    if status_filter:
        query = query.filter(models.Task.status == status_filter.upper())
    if priority_filter:
        query = query.filter(models.Task.priority == priority_filter.upper())
    
    tasks = query.order_by(models.Task.created_at.desc()).all()
    return tasks

@router.post("", response_model=schemas.TaskResponse)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_task = models.Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority.upper(),
        status=task_in.status.upper(),
        due_date=task_in.due_date,
        estimated_minutes=task_in.estimated_minutes,
        actual_minutes=task_in.actual_minutes
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # --- Convert task creation to RAG Memory ---
    mem_text = rag_service.format_task_memory("CREATE", {
        "title": new_task.title,
        "priority": new_task.priority,
        "estimated_minutes": new_task.estimated_minutes,
        "due_date": new_task.due_date.strftime("%Y-%m-%d") if new_task.due_date else None
    })
    rag_service.store_memory(current_user.id, mem_text, "CREATE", new_task.id)

    return new_task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    prev_due = task.due_date
    prev_status = task.status

    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "priority" and value:
            setattr(task, field, value.upper())
        elif field == "status" and value:
            setattr(task, field, value.upper())
        else:
            setattr(task, field, value)

    # Check if marked completed
    if task.status == "COMPLETED" and not task.completed_at:
        task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)

    # --- Convert task update/delay to RAG Memory ---
    if prev_due and task.due_date and task.due_date > prev_due:
        mem_text = rag_service.format_task_memory("DELAY", {
            "title": task.title,
            "priority": task.priority,
            "delay_note": f"due date moved from {prev_due.strftime('%Y-%m-%d')} to {task.due_date.strftime('%Y-%m-%d')}"
        })
        rag_service.store_memory(current_user.id, mem_text, "DELAY", task.id)
    elif task.status == "COMPLETED" and prev_status != "COMPLETED":
        mem_text = rag_service.format_task_memory("COMPLETE", {
            "title": task.title,
            "estimated_minutes": task.estimated_minutes,
            "actual_minutes": task.actual_minutes
        })
        rag_service.store_memory(current_user.id, mem_text, "COMPLETE", task.id)
    else:
        mem_text = rag_service.format_task_memory("UPDATE", {
            "title": task.title,
            "status": task.status,
            "actual_minutes": task.actual_minutes
        })
        rag_service.store_memory(current_user.id, mem_text, "UPDATE", task.id)

    return task

@router.patch("/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(
    task_id: int,
    actual_minutes: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    if actual_minutes is not None:
        task.actual_minutes = actual_minutes

    db.commit()
    db.refresh(task)

    # Store RAG memory
    mem_text = rag_service.format_task_memory("COMPLETE", {
        "title": task.title,
        "estimated_minutes": task.estimated_minutes,
        "actual_minutes": task.actual_minutes
    })
    rag_service.store_memory(current_user.id, mem_text, "COMPLETE", task.id)

    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    db.delete(task)
    db.commit()

    # Store deletion memory
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    mem_text = f"Deleted task '{title}' on {now_str}."
    rag_service.store_memory(current_user.id, mem_text, "DELETE", task_id)

    return {"detail": "Task successfully deleted"}
