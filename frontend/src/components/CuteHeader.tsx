import React from 'react';
import { User } from '../types';
import { Flame, Sparkles, LogIn, LogOut, CheckCircle2, Heart } from 'lucide-react';

interface Props {
  user: User | null;
  streakDays: number;
  completedToday: number;
  activeTab: 'tasks' | 'analytics' | 'assistant';
  setActiveTab: (tab: 'tasks' | 'analytics' | 'assistant') => void;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const CuteHeader: React.FC<Props> = ({
  user,
  streakDays,
  completedToday: _completedToday,
  activeTab,
  setActiveTab,
  onOpenAuth,
  onLogout
}) => {
  return (
    <header className="sticky top-0 z-40 bg-[#FAF6F0]/90 backdrop-blur-md border-b border-[#FFDFE5] py-4 px-4 sm:px-8">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Logo & Cute Mascot */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-3xl bg-gradient-to-tr from-[#FFDFE5] to-[#FF8DA1] flex items-center justify-center shadow-cozy animate-float">
            <span className="text-2xl">🐱🌸</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-[#4A3E3D] font-sans">
                Cozy Tracker
              </h1>
              <span className="text-xs bg-[#FFDFE5] text-[#FF8DA1] font-semibold px-2.5 py-0.5 rounded-full border border-[#FF8DA1]/30 flex items-center gap-1">
                <Heart className="w-3 h-3 fill-current" /> RAG AI
              </span>
            </div>
            <p className="text-xs text-[#9CA3AF]">Soft & Cozy AI Task Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center bg-white p-1.5 rounded-full shadow-soft border border-[#FFDFE5]/60">
          <button
            onClick={() => setActiveTab('tasks')}
            className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'tasks'
                ? 'bg-[#FFDFE5] text-[#FF8DA1] shadow-sm scale-105'
                : 'text-[#4A3E3D] hover:text-[#FF8DA1]'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" /> Tasks
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'analytics'
                ? 'bg-[#FEF3C7] text-[#D97706] shadow-sm scale-105'
                : 'text-[#4A3E3D] hover:text-[#D97706]'
            }`}
          >
            <Sparkles className="w-4 h-4" /> Analytics
          </button>

          <button
            onClick={() => setActiveTab('assistant')}
            className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'assistant'
                ? 'bg-[#EDE9FE] text-[#8B5CF6] shadow-sm scale-105'
                : 'text-[#4A3E3D] hover:text-[#8B5CF6]'
            }`}
          >
            <span className="text-sm">🤖</span> RAG Assistant
          </button>
        </nav>

        {/* Streak & User Profile Badge */}
        <div className="flex items-center gap-3">
          {/* Streak Counter */}
          <div className="flex items-center gap-1.5 bg-[#FEF3C7] text-[#D97706] px-3.5 py-1.5 rounded-full border border-[#FDE68A] text-xs font-bold shadow-soft">
            <Flame className="w-4 h-4 text-[#F59E0B] fill-current animate-bounce" />
            <span>{streakDays} Day Streak!</span>
          </div>

          {user ? (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium bg-white px-3 py-1.5 rounded-full border border-[#FFDFE5] text-[#4A3E3D]">
                🌸 {user.name}
              </span>
              <button
                onClick={onLogout}
                title="Logout"
                className="p-2 text-[#9CA3AF] hover:text-[#FF8DA1] transition-colors rounded-full hover:bg-white"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="bg-[#FF8DA1] hover:bg-[#ff7b92] text-white text-xs font-semibold px-4 py-2 rounded-full transition-all shadow-cozy hover:shadow-cozy-hover flex items-center gap-1.5"
            >
              <LogIn className="w-3.5 h-3.5" /> Sign In
            </button>
          )}
        </div>

      </div>
    </header>
  );
};
