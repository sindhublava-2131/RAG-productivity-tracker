import React, { useState } from 'react';
import { AuthService } from '../services/api';
import { User } from '../types';
import { X, Heart, Lock, Mail, User as UserIcon } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await AuthService.login(email, password);
        onSuccess(res.user);
      } else {
        const res = await AuthService.register(name, email, password);
        onSuccess(res.user);
      }
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Try demo credentials!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-fade-in">
      <div className="bg-white w-full max-w-md rounded-4xl p-6 sm:p-8 shadow-cozy border border-[#FFDFE5] relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-[#9CA3AF] hover:text-[#FF8DA1] p-1 rounded-full hover:bg-[#FAF6F0]"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-[#FFDFE5] rounded-full flex items-center justify-center mx-auto mb-2 text-2xl">
            🌸
          </div>
          <h2 className="text-2xl font-bold text-[#4A3E3D]">
            {isLogin ? 'Welcome Back!' : 'Join Cozy Tracker'}
          </h2>
          <p className="text-xs text-[#9CA3AF] mt-1">
            {isLogin ? 'Sign in to sync your RAG productivity memories' : 'Create a cute workspace to track your tasks'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-2xl text-xs border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Your Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-[#9CA3AF] absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Cozy Buddy 🌸"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#FAF6F0] rounded-2xl text-sm border border-[#FFDFE5] focus:outline-none focus:ring-2 focus:ring-[#FF8DA1]"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[#9CA3AF] absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                placeholder="demo@cozy.app"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#FAF6F0] rounded-2xl text-sm border border-[#FFDFE5] focus:outline-none focus:ring-2 focus:ring-[#FF8DA1]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#9CA3AF] absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#FAF6F0] rounded-2xl text-sm border border-[#FFDFE5] focus:outline-none focus:ring-2 focus:ring-[#FF8DA1]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#FF8DA1] hover:bg-[#ff7b92] text-white font-bold rounded-2xl shadow-cozy transition-all flex items-center justify-center gap-2 mt-2"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In 🌸' : 'Create Account 🚀')}
          </button>
        </form>

        <div className="mt-5 text-center text-xs text-[#9CA3AF]">
          {isLogin ? (
            <p>
              Don't have an account?{' '}
              <button onClick={() => setIsLogin(false)} className="text-[#FF8DA1] font-bold hover:underline">
                Sign Up
              </button>
            </p>
          ) : (
            <p>
              Already registered?{' '}
              <button onClick={() => setIsLogin(true)} className="text-[#FF8DA1] font-bold hover:underline">
                Sign In
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
