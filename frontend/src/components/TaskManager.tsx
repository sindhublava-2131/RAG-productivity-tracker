import React, { useState } from 'react';
import { Task, PriorityType, StatusType } from '../types';
import { TaskService } from '../services/api';
import { Plus, Check, Clock, Calendar, Trash2, Edit3, AlertCircle, Filter, Search, Tag } from 'lucide-react';

interface Props {
  tasks: Task[];
  onTaskChange: () => void;
}

export const TaskManager: React.FC<Props> = ({ tasks, onTaskChange }) => {
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<PriorityType>('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [estimatedMinutes, setEstimatedMinutes] = useState(45);
  const [actualMinutes, setActualMinutes] = useState(0);

  const openCreateModal = () => {
    setEditingTask(null);
    setTitle('');
    setDescription('');
    setPriority('MEDIUM');
    setDueDate('');
    setEstimatedMinutes(45);
    setActualMinutes(0);
    setIsModalOpen(true);
  };

  const openEditModal = (task: Task) => {
    setEditingTask(task);
    setTitle(task.title);
    setDescription(task.description || '');
    setPriority(task.priority);
    setDueDate(task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '');
    setEstimatedMinutes(task.estimated_minutes);
    setActualMinutes(task.actual_minutes);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    if (editingTask) {
      await TaskService.updateTask(editingTask.id, {
        title,
        description,
        priority,
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        estimated_minutes: estimatedMinutes,
        actual_minutes: actualMinutes
      });
    } else {
      await TaskService.createTask({
        title,
        description,
        priority,
        status: 'PENDING',
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        estimated_minutes: estimatedMinutes,
        actual_minutes: 0
      });
    }

    setIsModalOpen(false);
    onTaskChange();
  };

  const handleComplete = async (task: Task) => {
    const timeSpent = prompt(`Time spent on '${task.title}' in minutes:`, `${task.estimated_minutes || 30}`);
    const minutes = timeSpent ? parseInt(timeSpent, 10) : task.estimated_minutes;
    await TaskService.completeTask(task.id, minutes);
    onTaskChange();
  };

  const handleDelete = async (id: number) => {
    if (confirm('Delete this task memory?')) {
      await TaskService.deleteTask(id);
      onTaskChange();
    }
  };

  // Filter tasks
  const filteredTasks = tasks.filter(t => {
    const matchesSearch = t.title.toLowerCase().includes(search.toLowerCase()) || 
                          (t.description && t.description.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = filterStatus === 'ALL' || t.status === filterStatus;
    const matchesPriority = filterPriority === 'ALL' || t.priority === filterPriority;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const getPriorityBadge = (p: PriorityType) => {
    switch (p) {
      case 'URGENT': return 'bg-[#FEE2E2] text-[#EF4444] border-red-200';
      case 'HIGH': return 'bg-[#FEF3C7] text-[#D97706] border-amber-200';
      case 'MEDIUM': return 'bg-[#E0F2FE] text-[#0284C7] border-sky-200';
      case 'LOW': return 'bg-[#F3F4F6] text-[#6B7280] border-gray-200';
    }
  };

  const getStatusBadge = (s: StatusType) => {
    switch (s) {
      case 'COMPLETED': return 'bg-[#D1FAE5] text-[#10B981]';
      case 'IN_PROGRESS': return 'bg-[#FEF3C7] text-[#D97706]';
      case 'OVERDUE': return 'bg-[#FEE2E2] text-[#EF4444]';
      default: return 'bg-[#EDE9FE] text-[#8B5CF6]';
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner & Quick Add */}
      <div className="bg-gradient-to-r from-[#FFDFE5] via-[#FFF8F3] to-[#EDE9FE] p-6 rounded-4xl border border-[#FFDFE5] shadow-soft flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[#4A3E3D] flex items-center gap-2">
            Tasks & RAG Memories 🌸
          </h2>
          <p className="text-xs text-[#9CA3AF] mt-1">
            Every task completed or updated generates a RAG natural language memory for your AI assistant.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="bg-[#FF8DA1] hover:bg-[#ff7b92] text-white font-bold px-6 py-3 rounded-full shadow-cozy hover:shadow-cozy-hover transition-all flex items-center gap-2"
        >
          <Plus className="w-5 h-5" /> Add Cozy Task
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-3xl shadow-soft border border-[#FFDFE5]/60 flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-[#9CA3AF] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] focus:outline-none focus:ring-2 focus:ring-[#FF8DA1]"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-[#FAF6F0] px-3 py-2 rounded-2xl text-xs border border-[#FFDFE5] font-medium text-[#4A3E3D] focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="COMPLETED">Completed</option>
            <option value="OVERDUE">Overdue</option>
          </select>

          {/* Priority Filter */}
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="bg-[#FAF6F0] px-3 py-2 rounded-2xl text-xs border border-[#FFDFE5] font-medium text-[#4A3E3D] focus:outline-none"
          >
            <option value="ALL">All Priorities</option>
            <option value="URGENT">Urgent</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Task Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredTasks.length === 0 ? (
          <div className="col-span-2 text-center py-12 bg-white rounded-4xl border border-dashed border-[#FFDFE5]">
            <span className="text-4xl">🐱💤</span>
            <p className="text-sm font-semibold text-[#4A3E3D] mt-2">No tasks found!</p>
            <p className="text-xs text-[#9CA3AF]">Click 'Add Cozy Task' above to create your first task.</p>
          </div>
        ) : (
          filteredTasks.map((t) => (
            <div
              key={t.id}
              className={`bg-white p-5 rounded-3xl border transition-all duration-300 shadow-soft hover:shadow-cozy relative flex flex-col justify-between ${
                t.status === 'COMPLETED' ? 'border-[#D1FAE5] opacity-90' : 'border-[#FFDFE5]'
              }`}
            >
              <div>
                {/* Header Pills */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${getPriorityBadge(t.priority)}`}>
                      {t.priority}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getStatusBadge(t.status)}`}>
                      {t.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openEditModal(t)}
                      className="p-1.5 text-[#9CA3AF] hover:text-[#FF8DA1] rounded-full hover:bg-[#FAF6F0]"
                      title="Edit Task"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(t.id)}
                      className="p-1.5 text-[#9CA3AF] hover:text-red-500 rounded-full hover:bg-[#FAF6F0]"
                      title="Delete Task"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Title & Description */}
                <h3 className={`text-base font-bold text-[#4A3E3D] ${t.status === 'COMPLETED' ? 'line-through text-[#9CA3AF]' : ''}`}>
                  {t.title}
                </h3>
                {t.description && (
                  <p className="text-xs text-[#9CA3AF] mt-1 line-clamp-2">
                    {t.description}
                  </p>
                )}
              </div>

              {/* Time Details & Actions */}
              <div className="mt-4 pt-3 border-t border-[#FAF6F0] flex items-center justify-between text-xs text-[#9CA3AF]">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-[#FF8DA1]" /> Est: {t.estimated_minutes}m
                  </span>
                  {t.actual_minutes > 0 && (
                    <span className="flex items-center gap-1 text-[#10B981] font-semibold">
                      Actual: {t.actual_minutes}m
                    </span>
                  )}
                  {t.due_date && (
                    <span className="flex items-center gap-1 text-[#D97706]">
                      <Calendar className="w-3 h-3" /> {new Date(t.due_date).toLocaleDateString()}
                    </span>
                  )}
                </div>

                {t.status !== 'COMPLETED' && (
                  <button
                    onClick={() => handleComplete(t)}
                    className="bg-[#D1FAE5] hover:bg-[#a7f3d0] text-[#10B981] text-xs font-bold px-3 py-1.5 rounded-full transition-all flex items-center gap-1 shadow-sm"
                  >
                    <Check className="w-3.5 h-3.5" /> Mark Done
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Task Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white w-full max-w-lg rounded-4xl p-6 sm:p-8 shadow-cozy border border-[#FFDFE5]">
            <h3 className="text-xl font-bold text-[#4A3E3D] mb-4">
              {editingTask ? 'Edit Task' : 'Create New Cozy Task 🌸'}
            </h3>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Task Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Complete Operating Systems Paging Lab"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#FAF6F0] rounded-2xl text-sm border border-[#FFDFE5] focus:ring-2 focus:ring-[#FF8DA1] outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Description</label>
                <textarea
                  placeholder="Detailed notes or assignment requirements..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-4 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] focus:ring-2 focus:ring-[#FF8DA1] outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as PriorityType)}
                    className="w-full px-3 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] outline-none font-medium"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Estimated Minutes</label>
                  <input
                    type="number"
                    min="5"
                    value={estimatedMinutes}
                    onChange={(e) => setEstimatedMinutes(parseInt(e.target.value, 10) || 0)}
                    className="w-full px-3 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Due Date & Time</label>
                  <input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] outline-none"
                  />
                </div>

                {editingTask && (
                  <div>
                    <label className="block text-xs font-semibold text-[#4A3E3D] mb-1">Actual Minutes Spent</label>
                    <input
                      type="number"
                      min="0"
                      value={actualMinutes}
                      onChange={(e) => setActualMinutes(parseInt(e.target.value, 10) || 0)}
                      className="w-full px-3 py-2 bg-[#FAF6F0] rounded-2xl text-xs border border-[#FFDFE5] outline-none"
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 text-xs font-bold text-[#9CA3AF] hover:text-[#4A3E3D]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-[#FF8DA1] hover:bg-[#ff7b92] text-white text-xs font-bold px-6 py-2.5 rounded-full shadow-cozy"
                >
                  Save Task & RAG Memory 🌸
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
