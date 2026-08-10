from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = "MEDIUM" # LOW, MEDIUM, HIGH, URGENT
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, OVERDUE
    due_date: Optional[datetime] = None
    estimated_minutes: int = 0
    actual_minutes: int = 0

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    completed_at: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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
    completion_by_weekday: Dict[str, int]
    completion_by_hour: Dict[str, int]

# --- RAG Memory & Assistant Schemas ---
class RAGQueryRequest(BaseModel):
    question: str
    provider: Optional[str] = "ollama"  # ollama, openai, gemini, grok
    model_name: Optional[str] = None

class MemoryItem(BaseModel):
    id: str
    memory_text: str
    action_type: str
    timestamp: str
    relevance_score: Optional[float] = None

class RAGQueryResponse(BaseModel):
    answer: str
    retrieved_memories: List[MemoryItem]
    evaluator_score: float
    retrieval_agent: str
    evaluator_agent: str
    query_agent: str
    execution_time_ms: float
