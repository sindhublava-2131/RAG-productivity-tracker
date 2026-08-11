import axios, { AxiosError } from 'axios';
import {
  AnalyticsData,
  MemoryListResponse,
  RAGResponse,
  Task,
  User,
} from '../types';

const API_BASE = '/api';
const TOKEN_KEY = 'cozy_token';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (onUnauthorized) {
        onUnauthorized();
      }
    }
    return Promise.reject(error);
  },
);

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function extractDetail(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string | string[] } | undefined;
    if (Array.isArray(data?.detail)) {
      return data!.detail!.map((d) => d).join('; ');
    }
    if (typeof data?.detail === 'string') {
      return data.detail;
    }
    if (!error.response) {
      return 'Network error — cannot reach the server. Please try again.';
    }
    return `Request failed (${error.response.status}).`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unknown error.';
}

function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0;
    return new ApiError(status, extractDetail(error));
  }
  return new ApiError(0, extractDetail(error));
}

export const AuthService = {
  async register(name: string, email: string, password: string): Promise<{ access_token: string; user: User }> {
    try {
      const res = await api.post('/auth/register', { name, email, password });
      localStorage.setItem(TOKEN_KEY, res.data.access_token);
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem(TOKEN_KEY, res.data.access_token);
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async getCurrentUser(): Promise<User> {
    try {
      const res = await api.get('/auth/me');
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
  },
};

export const TaskService = {
  async getTasks(): Promise<Task[]> {
    try {
      const res = await api.get('/tasks');
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async createTask(task: Partial<Task>): Promise<Task> {
    try {
      const res = await api.post('/tasks', task);
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async updateTask(id: number, updates: Partial<Task>): Promise<Task> {
    try {
      const res = await api.put(`/tasks/${id}`, updates);
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async completeTask(id: number, actualMinutes?: number): Promise<Task> {
    try {
      const res = await api.patch(`/tasks/${id}/complete`, null, {
        params: { actual_minutes: actualMinutes },
      });
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async deleteTask(id: number): Promise<void> {
    try {
      await api.delete(`/tasks/${id}`);
    } catch (e) {
      throw toApiError(e);
    }
  },
};

export const AnalyticsService = {
  async getAnalytics(): Promise<AnalyticsData> {
    try {
      const res = await api.get('/analytics');
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },
};

export const RAGService = {
  async queryAssistant(question: string, provider: string = 'ollama'): Promise<RAGResponse> {
    try {
      const res = await api.post('/rag/query', { question, provider });
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async getMemories(): Promise<MemoryListResponse> {
    try {
      const res = await api.get('/rag/memories');
      return res.data;
    } catch (e) {
      throw toApiError(e);
    }
  },

  async deleteMemory(id: string): Promise<void> {
    try {
      await api.delete(`/rag/memories/${id}`);
    } catch (e) {
      throw toApiError(e);
    }
  },
};
