import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskManager } from './TaskManager';
import { TaskService } from '../services/api';

vi.mock('../services/api', () => ({
  TaskService: {
    createTask: vi.fn(),
    updateTask: vi.fn(),
    completeTask: vi.fn(),
    deleteTask: vi.fn(),
  },
}));

const mockedTaskService = vi.mocked(TaskService);

const sampleTasks = [
  {
    id: 1,
    user_id: 1,
    title: 'Study React',
    description: 'Build a component',
    priority: 'HIGH',
    status: 'PENDING',
    created_at: '2026-08-01T09:00:00Z',
    estimated_minutes: 60,
    actual_minutes: 0,
  },
  {
    id: 2,
    user_id: 1,
    title: 'Study Python',
    priority: 'LOW',
    status: 'COMPLETED',
    created_at: '2026-08-02T09:00:00Z',
    completed_at: '2026-08-02T10:00:00Z',
    estimated_minutes: 30,
    actual_minutes: 25,
  },
] as const;

describe('TaskManager', () => {
  it('renders task titles and empty state', () => {
    render(<TaskManager tasks={[...sampleTasks]} onTaskChange={() => {}} />);
    expect(screen.getByText('Study React')).toBeInTheDocument();
    expect(screen.getByText('Study Python')).toBeInTheDocument();
  });

  it('shows empty state when there are no tasks', () => {
    render(<TaskManager tasks={[]} onTaskChange={() => {}} />);
    expect(screen.getByText(/No tasks found/i)).toBeInTheDocument();
  });

  it('filters tasks by search text', () => {
    render(<TaskManager tasks={[...sampleTasks]} onTaskChange={() => {}} />);
    const search = screen.getByPlaceholderText(/Search tasks/i);
    fireEvent.change(search, { target: { value: 'python' } });
    expect(screen.queryByText('Study React')).not.toBeInTheDocument();
    expect(screen.getByText('Study Python')).toBeInTheDocument();
  });

  it('opens the complete modal and completes a task with entered minutes', async () => {
    mockedTaskService.completeTask.mockResolvedValue({ ...sampleTasks[0], status: 'COMPLETED' } as never);

    const onTaskChange = vi.fn();
    render(<TaskManager tasks={[...sampleTasks]} onTaskChange={onTaskChange} />);

    fireEvent.click(screen.getAllByText('Mark Done')[0]);
    expect(screen.getByText('Complete Task 🌸')).toBeInTheDocument();

    const minutesInput = screen.getByLabelText(/Actual minutes spent/i);
    fireEvent.change(minutesInput, { target: { value: '45' } });
    fireEvent.click(screen.getByText('Mark as Done ✓'));

    await waitFor(() => {
      expect(mockedTaskService.completeTask).toHaveBeenCalledWith(1, 45);
      expect(onTaskChange).toHaveBeenCalled();
    });
  });

  it('opens the delete confirmation modal and deletes', async () => {
    mockedTaskService.deleteTask.mockResolvedValue(undefined as never);

    const onTaskChange = vi.fn();
    render(<TaskManager tasks={[...sampleTasks]} onTaskChange={onTaskChange} />);

    const deleteButtons = screen.getAllByTitle('Delete Task');
    fireEvent.click(deleteButtons[0]);
    expect(screen.getByText('Delete Task?')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Delete Task'));
    await waitFor(() => {
      expect(mockedTaskService.deleteTask).toHaveBeenCalledWith(1);
      expect(onTaskChange).toHaveBeenCalled();
    });
  });
});
