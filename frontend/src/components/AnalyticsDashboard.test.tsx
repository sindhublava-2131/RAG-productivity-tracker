import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnalyticsDashboard } from './AnalyticsDashboard';

const analytics = {
  daily_completion: 3,
  weekly_completion: 12,
  monthly_progress_pct: 60.0,
  current_streak_days: 4,
  completion_rate_pct: 75.0,
  total_tasks: 20,
  completed_tasks: 15,
  pending_tasks: 5,
  overdue_tasks: 2,
  high_priority_completion_pct: 80.0,
  avg_completion_minutes: 45.0,
  completion_by_weekday: { Mon: 2, Tue: 3, Wed: 1, Thu: 4, Fri: 5, Sat: 0, Sun: 0 },
  completion_by_hour: {
    '08:00': 2, '09:00': 3, '10:00': 1, '11:00': 0, '12:00': 0,
    '13:00': 0, '14:00': 0, '15:00': 0, '16:00': 0, '17:00': 0,
    '18:00': 0, '19:00': 0, '20:00': 0, '21:00': 0, '22:00': 0,
    '23:00': 0, '00:00': 0, '01:00': 0, '02:00': 0, '03:00': 0,
    '04:00': 0, '05:00': 0, '06:00': 0, '07:00': 0,
  },
};

describe('AnalyticsDashboard', () => {
  it('shows the empty state when no analytics are provided', () => {
    render(<AnalyticsDashboard analytics={null} onRefresh={() => {}} />);
    expect(screen.getByText(/No analytics available yet/i)).toBeInTheDocument();
  });

  it('renders key metrics from the analytics prop', () => {
    render(<AnalyticsDashboard analytics={analytics} onRefresh={() => {}} />);
    expect(screen.getByText('Your Weekly Rhythm & Insights')).toBeInTheDocument();
    expect(screen.getByText(/4 Days/)).toBeInTheDocument();
    expect(screen.getByText(/45m/)).toBeInTheDocument();
  });

  it('calls onRefresh from the refresh button in the empty state', () => {
    const onRefresh = vi.fn();
    render(<AnalyticsDashboard analytics={null} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByText('Refresh'));
    expect(onRefresh).toHaveBeenCalled();
  });
});
