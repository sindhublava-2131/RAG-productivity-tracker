import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AIAssistant } from './AIAssistant';
import { RAGService } from '../services/api';

vi.mock('../services/api', () => ({
  RAGService: {
    queryAssistant: vi.fn(),
    getMemories: vi.fn(),
  },
}));

const mockedRAGService = vi.mocked(RAGService);

describe('AIAssistant', () => {
  it('renders the assistant header', () => {
    mockedRAGService.getMemories.mockResolvedValue({
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
      has_more: false,
    });
    render(<AIAssistant />);
    expect(screen.getByText(/Ask AI About Your Productivity Patterns/i)).toBeInTheDocument();
  });

  it('displays grounded answer with sources after asking', async () => {
    mockedRAGService.getMemories.mockResolvedValue({
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
      has_more: false,
    });
    mockedRAGService.queryAssistant.mockResolvedValue({
      answer: 'You finish high-priority tasks fastest in the morning.',
      sources: [
        {
          id: 'mem_123',
          task_id: 1,
          content: 'Completed report in 30 minutes.',
          action: 'COMPLETE',
          created_at: '2026-08-11T09:00:00Z',
          score: 0.9,
        },
      ],
      confidence: 0.85,
      grounded: true,
      retrieval_count: 1,
      provider: 'ollama',
      model: 'llama3',
      execution_time_ms: 42.5,
    });

    render(<AIAssistant />);
    const input = screen.getByPlaceholderText(/Ask about your task history/i);
    fireEvent.change(input, { target: { value: 'When am I most productive?' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText(/You finish high-priority tasks fastest in the morning\./i)).toBeInTheDocument();
    });
    expect(screen.getByText('Grounded')).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument();
    expect(screen.getByText('COMPLETE')).toBeInTheDocument();
  });

  it('shows error message when the query fails', async () => {
    mockedRAGService.getMemories.mockResolvedValue({
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
      has_more: false,
    });
    mockedRAGService.queryAssistant.mockRejectedValue(new Error('Cannot reach the server.'));

    render(<AIAssistant />);
    const input = screen.getByPlaceholderText(/Ask about your task history/i);
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText(/Cannot reach the server\./i)).toBeInTheDocument();
    });
  });
});
