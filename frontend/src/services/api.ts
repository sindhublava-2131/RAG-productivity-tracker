import axios from 'axios';
import { User, Task, AnalyticsData, RAGResponse, MemoryItem } from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cozy_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Mock Data Engine for Instant Standalone Web Preview ---
let mockTasks: Task[] = [
  {
    id: 1,
    user_id: 1,
    title: 'Complete React Component Architecture Assignment',
    description: 'Build modular TypeScript components with Tailwind styling',
    priority: 'HIGH',
    status: 'COMPLETED',
    due_date: new Date(Date.now() - 3600000 * 5).toISOString(),
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    estimated_minutes: 60,
    actual_minutes: 45
  },
  {
    id: 2,
    user_id: 1,
    title: 'Practice LeetCode & DSA Graph Algorithms',
    description: 'Solve 3 Dijkstra and Topological Sort problems',
    priority: 'URGENT',
    status: 'COMPLETED',
    due_date: new Date(Date.now() - 3600000 * 20).toISOString(),
    created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 18).toISOString(),
    estimated_minutes: 90,
    actual_minutes: 110
  },
  {
    id: 3,
    user_id: 1,
    title: 'Database Indexing & Query Optimization Assignment',
    description: 'Analyze B-Tree vs Hash indexes performance',
    priority: 'MEDIUM',
    status: 'PENDING',
    due_date: new Date(Date.now() + 3600000 * 24).toISOString(),
    created_at: new Date(Date.now() - 3600000 * 10).toISOString(),
    estimated_minutes: 45,
    actual_minutes: 0
  },
  {
    id: 4,
    user_id: 1,
    title: 'Setup Docker Compose Orchestration',
    description: 'Configure multi-stage container build for FastAPI & React',
    priority: 'HIGH',
    status: 'PENDING',
    due_date: new Date(Date.now() + 3600000 * 48).toISOString(),
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    estimated_minutes: 30,
    actual_minutes: 0
  },
  {
    id: 5,
    user_id: 1,
    title: 'Revise Operating Systems Memory Management',
    description: 'Paging, Segmentation, and Virtual Memory concepts',
    priority: 'LOW',
    status: 'PENDING',
    due_date: new Date(Date.now() + 3600000 * 72).toISOString(),
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    estimated_minutes: 60,
    actual_minutes: 0
  }
];

let mockMemories: MemoryItem[] = [
  { id: 'm1', memory_text: "Completed React assignment in 45 minutes before the deadline.", action_type: "COMPLETE", timestamp: new Date(Date.now() - 7200000).toISOString(), relevance_score: 0.95 },
  { id: 'm2', memory_text: "Postponed Database assignment three times last week.", action_type: "DELAY", timestamp: new Date(Date.now() - 86400000).toISOString(), relevance_score: 0.88 },
  { id: 'm3', memory_text: "Finished DSA practice two days late after deep debugging.", action_type: "COMPLETE", timestamp: new Date(Date.now() - 172800000).toISOString(), relevance_score: 0.82 },
  { id: 'm4', memory_text: "High-priority tasks are completed 30% faster during morning hours.", action_type: "PATTERN", timestamp: new Date(Date.now() - 259200000).toISOString(), relevance_score: 0.90 }
];

export const AuthService = {
  async register(name: string, email: string, password: string) {
    try {
      const res = await api.post('/auth/register', { name, email, password });
      localStorage.setItem('cozy_token', res.data.access_token);
      return res.data;
    } catch (e) {
      // Fallback local registration for preview
      const user: User = { id: 1, name, email, created_at: new Date().toISOString() };
      localStorage.setItem('cozy_token', 'mock_token_123');
      return { access_token: 'mock_token_123', user };
    }
  },

  async login(email: string, password: string) {
    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('cozy_token', res.data.access_token);
      return res.data;
    } catch (e) {
      // Fallback local login for preview
      const user: User = { id: 1, name: email.split('@')[0] || "Cozy User 🌸", email, created_at: new Date().toISOString() };
      localStorage.setItem('cozy_token', 'mock_token_123');
      return { access_token: 'mock_token_123', user };
    }
  },

  async getCurrentUser() {
    try {
      const res = await api.get('/auth/me');
      return res.data;
    } catch (e) {
      return { id: 1, name: "Cozy User 🌸", email: "demo@cozy.app", created_at: new Date().toISOString() };
    }
  },

  logout() {
    localStorage.removeItem('cozy_token');
  }
};

export const TaskService = {
  async getTasks(): Promise<Task[]> {
    try {
      const res = await api.get('/tasks');
      return res.data;
    } catch (e) {
      return [...mockTasks];
    }
  },

  async createTask(task: Partial<Task>): Promise<Task> {
    try {
      const res = await api.post('/tasks', task);
      return res.data;
    } catch (e) {
      const newTask: Task = {
        id: Date.now(),
        user_id: 1,
        title: task.title || 'Untitled Task',
        description: task.description || '',
        priority: (task.priority as any) || 'MEDIUM',
        status: (task.status as any) || 'PENDING',
        due_date: task.due_date,
        created_at: new Date().toISOString(),
        estimated_minutes: task.estimated_minutes || 30,
        actual_minutes: 0
      };
      mockTasks = [newTask, ...mockTasks];
      mockMemories.unshift({
        id: `m_${newTask.id}`,
        memory_text: `Created ${newTask.priority} task '${newTask.title}'.`,
        action_type: 'CREATE',
        timestamp: new Date().toISOString(),
        relevance_score: 0.9
      });
      return newTask;
    }
  },

  async updateTask(id: number, updates: Partial<Task>): Promise<Task> {
    try {
      const res = await api.put(`/tasks/${id}`, updates);
      return res.data;
    } catch (e) {
      mockTasks = mockTasks.map(t => t.id === id ? { ...t, ...updates } : t);
      const updated = mockTasks.find(t => t.id === id)!;
      return updated;
    }
  },

  async completeTask(id: number, actualMinutes?: number): Promise<Task> {
    try {
      const res = await api.patch(`/tasks/${id}/complete`, null, { params: { actual_minutes: actualMinutes } });
      return res.data;
    } catch (e) {
      mockTasks = mockTasks.map(t => t.id === id ? {
        ...t,
        status: 'COMPLETED',
        completed_at: new Date().toISOString(),
        actual_minutes: actualMinutes || t.estimated_minutes
      } : t);
      const updated = mockTasks.find(t => t.id === id)!;
      mockMemories.unshift({
        id: `m_comp_${id}`,
        memory_text: `Completed '${updated.title}' in ${updated.actual_minutes} minutes.`,
        action_type: 'COMPLETE',
        timestamp: new Date().toISOString(),
        relevance_score: 0.98
      });
      return updated;
    }
  },

  async deleteTask(id: number): Promise<void> {
    try {
      await api.delete(`/tasks/${id}`);
    } catch (e) {
      const t = mockTasks.find(x => x.id === id);
      mockTasks = mockTasks.filter(x => x.id !== id);
      if (t) {
        mockMemories.unshift({
          id: `m_del_${id}`,
          memory_text: `Deleted task '${t.title}'.`,
          action_type: 'DELETE',
          timestamp: new Date().toISOString(),
          relevance_score: 0.7
        });
      }
    }
  }
};

export const AnalyticsService = {
  async getAnalytics(): Promise<AnalyticsData> {
    try {
      const res = await api.get('/analytics');
      return res.data;
    } catch (e) {
      const total = mockTasks.length;
      const completed = mockTasks.filter(t => t.status === 'COMPLETED').length;
      return {
        daily_completion: 1,
        weekly_completion: completed,
        monthly_progress_pct: Math.round((completed / total) * 100),
        current_streak_days: 4,
        completion_rate_pct: Math.round((completed / total) * 100),
        total_tasks: total,
        completed_tasks: completed,
        pending_tasks: total - completed,
        overdue_tasks: 0,
        high_priority_completion_pct: 100,
        avg_completion_minutes: 77.5,
        completion_by_weekday: { Mon: 2, Tue: 1, Wed: 3, Thu: 0, Fri: 1, Sat: 0, Sun: 0 },
        completion_by_hour: { "09:00": 1, "11:00": 2, "14:00": 1, "16:00": 1 }
      };
    }
  }
};

export const RAGService = {
  async queryAssistant(question: string, provider: string = 'ollama'): Promise<RAGResponse> {
    try {
      const res = await api.post('/rag/query', { question, provider });
      return res.data;
    } catch (e) {
      // Mock Fallback RAG response generator
      const q = question.toLowerCase();
      let answer = "";
      if (q.includes("procrastinat") || q.includes("delay")) {
        answer = "Based on your memory log, you tend to postpone database assignments when multiple exams overlap! 💡 Recommendation: Break database tasks into 15-minute chunk sessions.";
      } else if (q.includes("perform") || q.includes("week")) {
        answer = "You had a great week! 🎉 You completed 2 high-priority coding assignments with a 100% completion rate on high-priority tasks.";
      } else if (q.includes("productive")) {
        answer = "Your peak productivity window is between 9:00 AM and 1:00 PM ☀️. You complete tasks 25% faster in the morning!";
      } else {
        answer = `Hello! Based on your 4 recorded task memories, you are maintaining a 4-day completion streak! Keep up the cozy momentum! 🌸`;
      }

      return {
        answer,
        retrieved_memories: mockMemories.slice(0, 3),
        evaluator_score: 0.92,
        retrieval_agent: "VectorHybridRetrievalAgent (ChromaDB + SentenceTransformers)",
        evaluator_agent: "RelevanceConfidenceEvaluator",
        query_agent: `MultiLLMQueryAgent (${provider.toUpperCase()})`,
        execution_time_ms: 142.5
      };
    }
  },

  async getMemories(): Promise<MemoryItem[]> {
    try {
      const res = await api.get('/rag/memories');
      return res.data;
    } catch (e) {
      return [...mockMemories];
    }
  }
};
