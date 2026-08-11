import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from './App';
import { AuthService, TaskService, AnalyticsService, RAGService, setUnauthorizedHandler } from './services/api';

vi.mock('./services/api', () => ({
  AuthService: {
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    login: vi.fn(),
  },
  TaskService: { getTasks: vi.fn() },
  AnalyticsService: { getAnalytics: vi.fn() },
  RAGService: { queryAssistant: vi.fn(), getMemories: vi.fn() },
  setUnauthorizedHandler: vi.fn(),
}));

const mockedAuthService = vi.mocked(AuthService);
const mockedTaskService = vi.mocked(TaskService);
const mockedAnalyticsService = vi.mocked(AnalyticsService);
const mockedRAGService = vi.mocked(RAGService);
const mockedSetUnauthorizedHandler = vi.mocked(setUnauthorizedHandler);

function emptyAnalytics() {
  return {
    daily_completion: 1,
    weekly_completion: 2,
    monthly_progress_pct: 10,
    current_streak_days: 1,
    completion_rate_pct: 50,
    total_tasks: 2,
    completed_tasks: 1,
    pending_tasks: 1,
    overdue_tasks: 0,
    high_priority_completion_pct: 0,
    avg_completion_minutes: 30,
    completion_by_weekday: { Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0, Sun: 0 },
    completion_by_hour: Object.fromEntries(
      Array.from({ length: 24 }, (_, h) => [`${String(h).padStart(2, '0')}:00`, 0]),
    ),
  };
}

describe('App', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mockedAuthService.logout.mockResolvedValue(undefined as never);
    mockedTaskService.getTasks.mockResolvedValue([] as never);
    mockedAnalyticsService.getAnalytics.mockResolvedValue(emptyAnalytics() as never);
    mockedRAGService.getMemories.mockResolvedValue({
      items: [], total: 0, limit: 50, offset: 0, has_more: false,
    } as never);
    mockedRAGService.queryAssistant.mockResolvedValue({
      answer: 'ok', sources: [], confidence: 0.9, grounded: true, retrieval_count: 0,
      provider: 'ollama', model: 'llama3', execution_time_ms: 12,
    } as never);
  });

  it('renders the header and opens the auth modal when logged out', async () => {
    mockedAuthService.getCurrentUser.mockRejectedValue(new Error('no token'));
    render(<App />);
    expect(await screen.findByText('Welcome Back!')).toBeInTheDocument();
  });

  it('registers the 401 handler on mount', () => {
    mockedAuthService.getCurrentUser.mockRejectedValue(new Error('no token'));
    render(<App />);
    expect(mockedSetUnauthorizedHandler).toHaveBeenCalled();
  });

  it('switches between tabs when authenticated', async () => {
    localStorage.setItem('cozy_token', 'fake-token');
    const user = { id: 1, name: 'Test', email: 't@dev.io', created_at: '' };
    mockedAuthService.getCurrentUser.mockResolvedValue(user as never);
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/🌸 Test/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Analytics'));
    expect(await screen.findByText('Your Weekly Rhythm & Insights')).toBeInTheDocument();

    fireEvent.click(screen.getByText(/RAG Assistant/));
    expect(await screen.findByText('Ask AI About Your Productivity Patterns')).toBeInTheDocument();
  });

  it('logs out when the header logout is triggered', async () => {
    localStorage.setItem('cozy_token', 'fake-token');
    const user = { id: 1, name: 'Test', email: 't@dev.io', created_at: '' };
    mockedAuthService.getCurrentUser.mockResolvedValue(user as never);
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTitle('Logout')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle('Logout'));
    await waitFor(() => {
      expect(mockedAuthService.logout).toHaveBeenCalled();
    });
  });
});
