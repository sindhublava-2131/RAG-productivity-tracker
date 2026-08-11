export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export type PriorityType = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type StatusType = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'OVERDUE';

export interface Task {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  priority: PriorityType;
  status: StatusType;
  due_date?: string;
  created_at: string;
  completed_at?: string;
  estimated_minutes: number;
  actual_minutes: number;
}

export interface AnalyticsData {
  daily_completion: number;
  weekly_completion: number;
  monthly_progress_pct: number;
  current_streak_days: number;
  completion_rate_pct: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  high_priority_completion_pct: number;
  avg_completion_minutes: number;
  completion_by_weekday: Record<string, number>;
  completion_by_hour: Record<string, number>;
}

export interface MemorySource {
  id: string;
  task_id: number | null;
  content: string;
  action: string | null;
  created_at: string | null;
  score: number;
}

export interface RAGResponse {
  answer: string;
  sources: MemorySource[];
  confidence: number;
  grounded: boolean;
  retrieval_count: number;
  provider: string;
  model: string;
  execution_time_ms: number;
}

export interface MemoryRecord {
  id: string;
  user_id: number;
  task_id: number | null;
  action: string | null;
  content: string;
  created_at: string;
  source_type: string | null;
  source_id: string | null;
  embedding_model: string | null;
  schema_version: number;
  task_title: string | null;
  priority: string | null;
  status: string | null;
  due_date: string | null;
  completed_at: string | null;
  estimated_minutes: number | null;
  actual_minutes: number | null;
}

export interface MemoryListResponse {
  items: MemoryRecord[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
