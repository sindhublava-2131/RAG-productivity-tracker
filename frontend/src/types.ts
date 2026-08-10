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

export interface MemoryItem {
  id: string;
  memory_text: string;
  action_type: string;
  timestamp: string;
  relevance_score?: number;
}

export interface RAGResponse {
  answer: string;
  retrieved_memories: MemoryItem[];
  evaluator_score: number;
  retrieval_agent: string;
  evaluator_agent: string;
  query_agent: string;
  execution_time_ms: number;
}
