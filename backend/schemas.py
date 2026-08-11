from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Enums ---
class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Status(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class TaskAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    COMPLETE = "COMPLETE"
    DELETE = "DELETE"
    DELAY = "DELAY"
    OVERDUE = "OVERDUE"


# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    due_date: datetime | None = None
    estimated_minutes: int = Field(default=0, ge=0)
    actual_minutes: int = Field(default=0, ge=0)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    due_date: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    completed_at: datetime | None = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    completed_at: datetime | None = None


# --- Analytics Schemas ---
class AnalyticsResponse(BaseModel):
    daily_completion: int
    weekly_completion: int
    monthly_progress_pct: float
    current_streak_days: int
    completion_rate_pct: float
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    high_priority_completion_pct: float
    avg_completion_minutes: float
    completion_by_weekday: dict[str, int]
    completion_by_hour: dict[str, int]


# --- RAG Memory & Assistant Schemas ---
class RAGQueryRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    question: str = Field(..., min_length=1, max_length=2000)
    provider: str | None = "ollama"
    model_name: str | None = None


class MemorySource(BaseModel):
    id: str
    task_id: int | None = None
    content: str
    action: str | None = None
    created_at: datetime | None = None
    score: float


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[MemorySource]
    confidence: float
    grounded: bool
    retrieval_count: int
    provider: str
    model: str
    execution_time_ms: float


class MemoryRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    task_id: int | None = None
    action: str | None = None
    content: str
    created_at: datetime
    source_type: str | None = None
    source_id: str | None = None
    embedding_model: str | None = None
    schema_version: int = 1
    task_title: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None


class MemoryListResponse(BaseModel):
    items: list[MemoryRecord]
    total: int
    limit: int
    offset: int
    has_more: bool


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, Any]
