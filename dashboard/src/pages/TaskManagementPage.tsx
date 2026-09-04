import React, { useEffect, useState } from 'react';
import { InvestigationTask } from '../types';
import { apiService } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export const TaskManagementPage: React.FC = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<InvestigationTask[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const res = await apiService.listInvestigationTasks();
      setTasks(res.data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleComplete = async (taskId: string) => {
    try {
      const res = await apiService.completeInvestigationTask(taskId);
      setTasks(tasks.map(t => t.task_id === taskId ? res.data : t));
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  const filteredTasks = tasks.filter(t => {
    if (statusFilter === 'ALL') return true;
    return t.status === statusFilter;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
              📋
            </span>
            Investigator Task & Team Workload Board
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Track forensic assignments, review due dates, and manage case progression tasks.
          </p>
        </div>

        <div className="flex gap-2">
          {['ALL', 'OPEN', 'IN_PROGRESS', 'COMPLETED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                statusFilter === st ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {filteredTasks.map((t) => (
          <div key={t.task_id} className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-indigo-400">{t.case_id}</span>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  t.priority === 'CRITICAL'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {t.priority}
              </span>
            </div>
            <h4 className="font-bold text-sm text-white">{t.title}</h4>
            <p className="text-xs text-slate-400 line-clamp-2">{t.description}</p>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Assignee: <strong className="text-slate-200">{t.assignee}</strong></span>
              {t.status !== 'COMPLETED' ? (
                <button
                  onClick={() => handleComplete(t.task_id)}
                  className="text-emerald-400 hover:text-emerald-300 font-semibold text-xs"
                >
                  ✓ Complete
                </button>
              ) : (
                <span className="text-emerald-400 font-semibold text-[11px]">✓ Completed</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskManagementPage;
