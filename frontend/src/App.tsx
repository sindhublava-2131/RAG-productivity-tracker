import React, { useState, useEffect } from 'react';
import { User, Task, AnalyticsData } from './types';
import { AuthService, TaskService, AnalyticsService } from './services/api';
import { CuteHeader } from './components/CuteHeader';
import { AuthModal } from './components/AuthModal';
import { TaskManager } from './components/TaskManager';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { AIAssistant } from './components/AIAssistant';
import { Heart, Sparkles, Database, ShieldCheck, Cpu } from 'lucide-react';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<'tasks' | 'analytics' | 'assistant'>('tasks');
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    const u = await AuthService.getCurrentUser();
    setUser(u);
    await reloadData();
  };

  const reloadData = async () => {
    const taskList = await TaskService.getTasks();
    setTasks(taskList);
    const stats = await AnalyticsService.getAnalytics();
    setAnalytics(stats);
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
    reloadData();
  };

  return (
    <div className="min-h-screen bg-[#FAF6F0] flex flex-col justify-between selection:bg-[#FFDFE5] selection:text-[#FF8DA1]">
      
      <div>
        {/* Cute Pastel Header */}
        <CuteHeader
          user={user}
          streakDays={analytics?.current_streak_days || 4}
          completedToday={analytics?.daily_completion || 1}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onOpenAuth={() => setIsAuthOpen(true)}
          onLogout={handleLogout}
        />

        {/* Main Content Area */}
        <main className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
          {activeTab === 'tasks' && (
            <TaskManager tasks={tasks} onTaskChange={reloadData} />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsDashboard />
          )}

          {activeTab === 'assistant' && (
            <AIAssistant />
          )}
        </main>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(u) => {
          setUser(u);
          reloadData();
        }}
      />

      {/* Cute Footer with Tech Stack Badges */}
      <footer className="border-t border-[#FFDFE5] bg-white/60 backdrop-blur-sm py-6 mt-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#9CA3AF]">
          <div className="flex items-center gap-2">
            <span>Cozy AI Productivity System</span>
            <span>•</span>
            <span className="flex items-center gap-1 text-[#FF8DA1] font-bold">
              Made with <Heart className="w-3.5 h-3.5 fill-current" /> for high productivity
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="bg-[#FAF6F0] px-2.5 py-1 rounded-full border border-[#FFDFE5] font-semibold text-[#4A3E3D]">
              FastAPI
            </span>
            <span className="bg-[#FAF6F0] px-2.5 py-1 rounded-full border border-[#FFDFE5] font-semibold text-[#4A3E3D]">
              React + TS
            </span>
            <span className="bg-[#FAF6F0] px-2.5 py-1 rounded-full border border-[#FFDFE5] font-semibold text-[#4A3E3D]">
              ChromaDB Vector RAG
            </span>
            <span className="bg-[#EDE9FE] px-2.5 py-1 rounded-full border border-[#EDE9FE] font-semibold text-[#8B5CF6]">
              SentenceTransformers
            </span>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default App;
