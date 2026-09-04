import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  ArrowUpRight,
  XCircle,
  Filter,
  ShieldAlert,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { EarlyWarning, EarlyWarningSeverity, EarlyWarningStatus } from '../types';

export const EarlyWarningPage: React.FC = () => {
  const [warnings, setWarnings] = useState<EarlyWarning[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const loadWarnings = async () => {
    try {
      setLoading(true);
      const res = await apiClient.listEarlyWarnings({
        severity: severityFilter as EarlyWarningSeverity || undefined,
        status: statusFilter as EarlyWarningStatus || undefined,
      });
      setWarnings(res.data);
    } catch (err) {
      console.error('Failed to load warnings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWarnings();
  }, [severityFilter, statusFilter]);

  const handleAction = async (warningId: string, action: 'acknowledge' | 'escalate' | 'dismiss') => {
    try {
      if (action === 'acknowledge') await apiClient.acknowledgeEarlyWarning(warningId, { notes: 'Acknowledged via workstation' });
      else if (action === 'escalate') await apiClient.escalateEarlyWarning(warningId, { notes: 'Escalated to investigation case' });
      else if (action === 'dismiss') await apiClient.dismissEarlyWarning(warningId, { notes: 'Dismissed by investigator' });
      await loadWarnings();
    } catch (err) {
      console.error(`Failed to ${action} warning:`, err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
              <AlertTriangle className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">Proactive Early Warning Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time proactive hazard triggers with investigator acknowledgment and non-destructive action workflows
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="ESCALATED">Escalated</option>
            <option value="DISMISSED">Dismissed</option>
          </select>

          <button
            onClick={loadWarnings}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading proactive warnings...</div>
      ) : (
        <div className="space-y-3">
          {warnings.map((w) => (
            <div
              key={w.warning_id}
              className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100 text-sm">{w.entity_type} {w.entity_id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {w.severity}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                    {w.status}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {w.status === 'ACTIVE' && (
                    <>
                      <button
                        onClick={() => handleAction(w.warning_id, 'acknowledge')}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-500/30 font-medium"
                      >
                        <CheckCircle className="h-3 w-3" /> Acknowledge
                      </button>
                      <button
                        onClick={() => handleAction(w.warning_id, 'escalate')}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 font-medium"
                      >
                        <ArrowUpRight className="h-3 w-3" /> Escalate
                      </button>
                      <button
                        onClick={() => handleAction(w.warning_id, 'dismiss')}
                        className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400"
                      >
                        <XCircle className="h-3 w-3" /> Dismiss
                      </button>
                    </>
                  )}
                </div>
              </div>

              <p className="text-slate-300">{w.explanation}</p>

              <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/80">
                <div className="flex items-center gap-3">
                  <span>Recommended: <strong className="text-amber-400">{w.recommended_action}</strong></span>
                  <span>•</span>
                  <span>Confidence: {Math.round(w.confidence * 100)}%</span>
                </div>
                <span className="text-[11px] text-slate-500">Created: {new Date(w.created_at).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
          {warnings.length === 0 && (
            <div className="p-8 text-center text-xs text-slate-500 italic">No warnings match the selected filters.</div>
          )}
        </div>
      )}
    </div>
  );
};
