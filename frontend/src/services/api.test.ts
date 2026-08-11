import { describe, expect, it, vi } from 'vitest';
import { AuthService, TaskService, RAGService, ApiError, api } from '../services/api';

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal<typeof import('axios').default>();
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: {},
  };
  const defaultExport = Object.assign(
    mockInstance,
    actual,
    { create: vi.fn(() => mockInstance) },
  );
  return { ...actual, default: defaultExport, create: defaultExport.create };
});

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('AuthService', () => {
  it('stores token on successful login', async () => {
    const user = { id: 1, name: 'Test', email: 'test@dev.io', created_at: '2026-01-01T00:00:00Z' };
    mockedApi.post.mockResolvedValue({
      data: { access_token: 'token123', user },
    });

    const res = await AuthService.login('test@dev.io', 'password123');

    expect(res.access_token).toBe('token123');
    expect(localStorage.getItem('cozy_token')).toBe('token123');
  });

  it('rejects with ApiError on failed login', async () => {
    mockedApi.post.mockRejectedValue({
      response: { status: 401, data: { detail: 'Invalid credentials' } },
    });

    await expect(AuthService.login('a@b.c', 'wrongpass')).rejects.toThrow(ApiError);
  });
});

describe('TaskService', () => {
  it('lists tasks', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const tasks = await TaskService.getTasks();
    expect(tasks).toEqual([]);
  });
});

describe('RAGService', () => {
  it('queries the assistant with provider', async () => {
    const ragResponse = {
      answer: 'You completed tasks faster in the morning.',
      sources: [],
      confidence: 0.9,
      grounded: true,
      retrieval_count: 0,
      provider: 'ollama',
      model: 'llama3',
      execution_time_ms: 12.3,
    };
    mockedApi.post.mockResolvedValue({ data: ragResponse });

    const res = await RAGService.queryAssistant('When am I most productive?', 'ollama');

    expect(mockedApi.post).toHaveBeenCalledWith('/rag/query', {
      question: 'When am I most productive?',
      provider: 'ollama',
    });
    expect(res.grounded).toBe(true);
    expect(res.sources).toEqual([]);
  });
});
