import React, { useState, useEffect } from 'react';
import { RAGResponse, MemoryItem } from '../types';
import { RAGService } from '../services/api';
import { Send, Bot, Sparkles, Brain, Cpu, ShieldCheck, Database, Layers, RefreshCw } from 'lucide-react';

export const AIAssistant: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [provider, setProvider] = useState('ollama');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    const list = await RAGService.getMemories();
    setMemories(list);
  };

  const handleAsk = async (qText?: string) => {
    const query = qText || question;
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    try {
      const res = await RAGService.queryAssistant(query, provider);
      setResponse(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const presetQuestions = [
    "How did I perform this week?",
    "Which tasks do I procrastinate on?",
    "When am I most productive?",
    "Compare this week with last week.",
    "Which high-priority tasks do I delay?",
    "Give me recommendations for tomorrow."
  ];

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#EDE9FE] via-[#FFF8F3] to-[#FFDFE5] p-6 rounded-4xl border border-[#EDE9FE] shadow-soft flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold bg-[#EDE9FE] text-[#8B5CF6] px-3 py-1 rounded-full border border-[#8B5CF6]/30">
            🤖 Multi-Agent RAG Memory Assistant
          </span>
          <h2 className="text-2xl font-bold text-[#4A3E3D] mt-2">
            Ask AI About Your Productivity Patterns
          </h2>
          <p className="text-xs text-[#9CA3AF]">
            Performs vector similarity search in ChromaDB before generating grounded insights.
          </p>
        </div>

        {/* LLM Provider Selector */}
        <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full border border-[#FFDFE5] shadow-soft">
          <Cpu className="w-4 h-4 text-[#8B5CF6]" />
          <span className="text-xs font-bold text-[#4A3E3D]">LLM Provider:</span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="bg-[#FAF6F0] px-3 py-1 rounded-xl text-xs font-bold text-[#8B5CF6] outline-none border border-[#EDE9FE]"
          >
            <option value="ollama">Ollama (Local Default)</option>
            <option value="openai">OpenAI (ChatGPT)</option>
            <option value="gemini">Google Gemini</option>
            <option value="grok">xAI Grok</option>
          </select>
        </div>
      </div>

      {/* Main Grid: Chat Assistant & Memory Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Column 1 & 2: Interactive Chat & RAG Output */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Preset Questions Pill Buttons */}
          <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft">
            <span className="text-xs font-bold text-[#9CA3AF] block mb-2.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#FF8DA1]" /> Quick Preset Questions:
            </span>
            <div className="flex flex-wrap gap-2">
              {presetQuestions.map((pq, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuestion(pq);
                    handleAsk(pq);
                  }}
                  className="bg-[#FAF6F0] hover:bg-[#FFDFE5] text-[#4A3E3D] hover:text-[#FF8DA1] text-xs font-semibold px-3 py-1.5 rounded-full border border-[#FFDFE5] transition-all"
                >
                  {pq}
                </button>
              ))}
            </div>
          </div>

          {/* Input Box */}
          <div className="bg-white p-4 rounded-3xl border border-[#FFDFE5] shadow-soft flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask about your task history, procrastination patterns, or focus hours..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              className="w-full px-4 py-2.5 bg-[#FAF6F0] rounded-2xl text-xs sm:text-sm border border-[#FFDFE5] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
            />
            <button
              onClick={() => handleAsk()}
              disabled={loading}
              className="bg-[#8B5CF6] hover:bg-[#7c3aed] text-white p-3 rounded-2xl shadow-cozy transition-all flex items-center justify-center shrink-0"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>

          {/* AI Response Card */}
          {loading && (
            <div className="bg-white p-6 rounded-4xl border border-[#EDE9FE] shadow-soft text-center py-10">
              <div className="w-10 h-10 border-4 border-[#EDE9FE] border-t-[#8B5CF6] rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-xs text-[#8B5CF6] font-semibold">Retrieving task memories from ChromaDB & evaluating relevancy...</p>
            </div>
          )}

          {response && !loading && (
            <div className="bg-white p-6 rounded-4xl border border-[#EDE9FE] shadow-soft space-y-4 animate-fade-in">
              <div className="flex items-center justify-between border-b border-[#FAF6F0] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-[#EDE9FE] flex items-center justify-center text-sm">
                    🤖
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#4A3E3D]">AI Assistant Answer</h3>
                    <span className="text-[10px] text-[#9CA3AF]">{response.query_agent}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] bg-[#D1FAE5] text-[#10B981] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Relevancy: {Math.round(response.evaluator_score * 100)}%
                  </span>
                  <span className="text-[10px] bg-[#FAF6F0] text-[#9CA3AF] px-2 py-0.5 rounded-full font-mono">
                    {response.execution_time_ms} ms
                  </span>
                </div>
              </div>

              {/* Formatted Answer */}
              <div className="text-xs sm:text-sm text-[#4A3E3D] leading-relaxed whitespace-pre-wrap font-sans bg-[#FAF6F0]/60 p-4 rounded-2xl border border-[#FFDFE5]/40">
                {response.answer}
              </div>

              {/* RAG Agent Pipeline Breakdown */}
              <div className="pt-2">
                <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-2">
                  ⚙️ Multi-Agent Execution Pipeline:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                  <div className="bg-[#FAF6F0] p-2.5 rounded-2xl border border-[#FFDFE5]">
                    <span className="font-bold text-[#8B5CF6] block">1. Retrieval Agent</span>
                    <span className="text-[10px] text-[#9CA3AF]">{response.retrieval_agent}</span>
                  </div>
                  <div className="bg-[#FAF6F0] p-2.5 rounded-2xl border border-[#FFDFE5]">
                    <span className="font-bold text-[#10B981] block">2. Evaluator Agent</span>
                    <span className="text-[10px] text-[#9CA3AF]">{response.evaluator_agent}</span>
                  </div>
                  <div className="bg-[#FAF6F0] p-2.5 rounded-2xl border border-[#FFDFE5]">
                    <span className="font-bold text-[#FF8DA1] block">3. Query Agent</span>
                    <span className="text-[10px] text-[#9CA3AF]">{response.query_agent}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Column 3: Live ChromaDB Memory Stream */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-4xl border border-[#FFDFE5] shadow-soft">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-[#4A3E3D] flex items-center gap-1.5">
                <Database className="w-4 h-4 text-[#FF8DA1]" /> RAG Memory Stream
              </h3>
              <button
                onClick={fetchMemories}
                className="text-[10px] text-[#FF8DA1] hover:underline flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </div>
            <p className="text-[11px] text-[#9CA3AF] mb-3">
              Live natural-language embeddings stored in ChromaDB for vector retrieval.
            </p>

            <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
              {memories.length === 0 ? (
                <p className="text-xs text-[#9CA3AF] text-center py-6">No memories recorded yet.</p>
              ) : (
                memories.map((m) => (
                  <div key={m.id} className="bg-[#FAF6F0] p-3 rounded-2xl border border-[#FFDFE5]/60 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-[#FFDFE5] text-[#FF8DA1]">
                        {m.action_type}
                      </span>
                      {m.relevance_score && (
                        <span className="text-[9px] font-bold text-[#10B981]">
                          Score: {Math.round(m.relevance_score * 100)}%
                        </span>
                      )}
                    </div>
                    <p className="text-[#4A3E3D] font-medium leading-tight">{m.memory_text}</p>
                    <span className="text-[9px] text-[#9CA3AF] block mt-1">
                      {new Date(m.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
