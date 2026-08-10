import React, { useEffect, useState } from 'react';
import { AnalyticsData } from '../types';
import { AnalyticsService } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { Flame, CheckCircle, Clock, Calendar, AlertTriangle, TrendingUp, Award, Zap } from 'lucide-react';

export const AnalyticsDashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    const res = await AnalyticsService.getAnalytics();
    setData(res);
    setLoading(false);
  };

  if (loading || !data) {
    return (
      <div className="text-center py-16">
        <div className="w-12 h-12 border-4 border-[#FFDFE5] border-t-[#FF8DA1] rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-xs text-[#9CA3AF]">Calculating cozy productivity analytics...</p>
      </div>
    );
  }

  // Formatting chart data
  const weekdayData = Object.entries(data.completion_by_weekday).map(([day, count]) => ({
    day,
    completed: count
  }));

  const hourData = Object.entries(data.completion_by_hour).map(([hour, count]) => ({
    hour,
    completed: count
  }));

  const pieData = [
    { name: 'Completed', value: data.completed_tasks, color: '#10B981' },
    { name: 'Pending', value: data.pending_tasks, color: '#FF8DA1' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Overview Metric Banner */}
      <div className="bg-gradient-to-r from-[#FFF8F3] via-[#FEF3C7] to-[#FFDFE5] p-6 rounded-4xl border border-[#FFDFE5] shadow-soft">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold bg-[#FFDFE5] text-[#FF8DA1] px-3 py-1 rounded-full border border-[#FF8DA1]/30">
              📊 Real-Time Productivity Metrics
            </span>
            <h2 className="text-2xl font-bold text-[#4A3E3D] mt-2">Your Weekly Rhythm & Insights</h2>
            <p className="text-xs text-[#9CA3AF]">Tracks task velocity, completion streaks, and focus windows.</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
              <span className="text-xs text-[#9CA3AF] block font-medium">Monthly Progress</span>
              <span className="text-2xl font-bold text-[#10B981]">{data.monthly_progress_pct}%</span>
            </div>
            <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
              <span className="text-xs text-[#9CA3AF] block font-medium">Completion Rate</span>
              <span className="text-2xl font-bold text-[#8B5CF6]">{data.completion_rate_pct}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* 11 Required Metrics Grid Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Metric 1: Daily Completion */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#D1FAE5] rounded-full flex items-center justify-center mx-auto mb-2 text-[#10B981]">
            <CheckCircle className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">Daily Completed</span>
          <p className="text-xl font-bold text-[#4A3E3D]">{data.daily_completion}</p>
        </div>

        {/* Metric 2: Weekly Completion */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#FEF3C7] rounded-full flex items-center justify-center mx-auto mb-2 text-[#D97706]">
            <Calendar className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">Weekly Done</span>
          <p className="text-xl font-bold text-[#4A3E3D]">{data.weekly_completion}</p>
        </div>

        {/* Metric 3: Current Streak */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#FFDFE5] rounded-full flex items-center justify-center mx-auto mb-2 text-[#FF8DA1]">
            <Flame className="w-4 h-4 fill-current" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">Current Streak</span>
          <p className="text-xl font-bold text-[#FF8DA1]">{data.current_streak_days} Days</p>
        </div>

        {/* Metric 4: Avg Completion Time */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#E0F2FE] rounded-full flex items-center justify-center mx-auto mb-2 text-[#0284C7]">
            <Clock className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">Avg Task Time</span>
          <p className="text-xl font-bold text-[#4A3E3D]">{data.avg_completion_minutes}m</p>
        </div>

        {/* Metric 5: Overdue Tasks */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#FEE2E2] rounded-full flex items-center justify-center mx-auto mb-2 text-[#EF4444]">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">Overdue Tasks</span>
          <p className="text-xl font-bold text-[#EF4444]">{data.overdue_tasks}</p>
        </div>

        {/* Metric 6: High-Priority Rate */}
        <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft text-center">
          <div className="w-8 h-8 bg-[#EDE9FE] rounded-full flex items-center justify-center mx-auto mb-2 text-[#8B5CF6]">
            <Zap className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-semibold text-[#9CA3AF]">High-Prio Rate</span>
          <p className="text-xl font-bold text-[#8B5CF6]">{data.high_priority_completion_pct}%</p>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Chart 1: Completion by Weekday (Bar Chart) */}
        <div className="bg-white p-6 rounded-4xl border border-[#FFDFE5] shadow-soft">
          <h3 className="text-base font-bold text-[#4A3E3D] mb-1 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#FF8DA1]" /> Tasks Completed by Weekday
          </h3>
          <p className="text-xs text-[#9CA3AF] mb-4">Distribution across Monday – Sunday</p>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weekdayData}>
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFDF9', borderRadius: '16px', border: '1px solid #FFDFE5' }}
                />
                <Bar dataKey="completed" fill="#FF8DA1" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Completed vs Pending Donut Chart */}
        <div className="bg-white p-6 rounded-4xl border border-[#FFDFE5] shadow-soft">
          <h3 className="text-base font-bold text-[#4A3E3D] mb-1 flex items-center gap-2">
            <Award className="w-4 h-4 text-[#10B981]" /> Completed vs Pending Ratio
          </h3>
          <p className="text-xs text-[#9CA3AF] mb-4">Total Task Volume Breakdown</p>

          <div className="h-60 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFDF9', borderRadius: '16px', border: '1px solid #FFDFE5' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 text-xs font-semibold">
            <span className="flex items-center gap-1.5 text-[#10B981]">
              <span className="w-3 h-3 rounded-full bg-[#10B981]"></span> Completed ({data.completed_tasks})
            </span>
            <span className="flex items-center gap-1.5 text-[#FF8DA1]">
              <span className="w-3 h-3 rounded-full bg-[#FF8DA1]"></span> Pending ({data.pending_tasks})
            </span>
          </div>
        </div>

        {/* Chart 3: Peak Productivity Hours Heatmap */}
        <div className="col-span-1 md:col-span-2 bg-white p-6 rounded-4xl border border-[#FFDFE5] shadow-soft">
          <h3 className="text-base font-bold text-[#4A3E3D] mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#8B5CF6]" /> Peak Completion Hours
          </h3>
          <p className="text-xs text-[#9CA3AF] mb-4">Task completion activity by hour of day</p>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourData}>
                <XAxis dataKey="hour" stroke="#9CA3AF" fontSize={10} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFDF9', borderRadius: '16px', border: '1px solid #FFDFE5' }}
                />
                <Area type="monotone" dataKey="completed" stroke="#8B5CF6" fill="#EDE9FE" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
};
