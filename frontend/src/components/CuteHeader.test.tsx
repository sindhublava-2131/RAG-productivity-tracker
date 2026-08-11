import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CuteHeader } from './CuteHeader';

const baseProps = {
  user: null,
  streakDays: 3,
  completedToday: 2,
  activeTab: 'tasks' as const,
  setActiveTab: vi.fn(),
  onOpenAuth: vi.fn(),
  onLogout: vi.fn(),
};

describe('CuteHeader', () => {
  it('renders the brand and streak', () => {
    render(<CuteHeader {...baseProps} />);
    expect(screen.getByText('Cozy Tracker')).toBeInTheDocument();
    expect(screen.getByText('3 Day Streak!')).toBeInTheDocument();
  });

  it('shows sign-in button when logged out and opens auth', () => {
    const onOpenAuth = vi.fn();
    render(<CuteHeader {...baseProps} onOpenAuth={onOpenAuth} />);
    fireEvent.click(screen.getByText('Sign In'));
    expect(onOpenAuth).toHaveBeenCalled();
  });

  it('shows the user name and logs out when authenticated', () => {
    const onLogout = vi.fn();
    render(<CuteHeader {...baseProps} user={{ id: 1, name: 'Cozy User', email: 'a@b.c', created_at: '' }} onLogout={onLogout} />);
    expect(screen.getByText('🌸 Cozy User')).toBeInTheDocument();
    fireEvent.click(screen.getByTitle('Logout'));
    expect(onLogout).toHaveBeenCalled();
  });

  it('switches tabs', () => {
    const setActiveTab = vi.fn();
    render(<CuteHeader {...baseProps} setActiveTab={setActiveTab} />);
    fireEvent.click(screen.getByText('Analytics'));
    expect(setActiveTab).toHaveBeenCalledWith('analytics');
  });
});
