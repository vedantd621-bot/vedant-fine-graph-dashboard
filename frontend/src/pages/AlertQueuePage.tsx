import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Clock,
  Filter,
  Search,
  UserCheck,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Eye,
  Layers,
  ArrowUpDown,
  RefreshCw,
} from 'lucide-react';
import { apiService } from '../api/client';
import {
  PrioritizedAlert,
  PriorityLevel,
  TriageStatus,
  SLAStatus,
  AlertPriorityExplanation,
} from '../types';

interface AlertQueuePageProps {
  onSelectAlert?: (alertId: string) => void;
  onSelectAccount?: (accountId: string) => void;
}

export const AlertQueuePage: React.FC<AlertQueuePageProps> = ({
  onSelectAlert,
  onSelectAccount,
}) => {
  const [alerts, setAlerts] = useState<PrioritizedAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('priority_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Modals state
  const [explanationAlertId, setExplanationAlertId] = useState<string | null>(null);
  const [explanationData, setExplanationData] = useState<AlertPriorityExplanation | null>(null);
  const [triageAlertId, setTriageAlertId] = useState<string | null>(null);
  const [selectedTriageStatus, setSelectedTriageStatus] = useState<TriageStatus>('INVESTIGATING');
  const [triageNotes, setTriageNotes] = useState<string>('');
  const [assignAlertId, setAssignAlertId] = useState<string | null>(null);
  const [selectedAssignee, setSelectedAssignee] = useState<string>('alice_investigator');

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params: any = {
        sort: sortBy,
        order: sortOrder,
        page_size: 50,
      };
      if (priorityFilter) params.priority = priorityFilter;
      if (statusFilter) params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await apiService.listPrioritizedAlerts(params);
      if (res && res.data) {
        setAlerts(res.data);
      }
    } catch (err) {
      console.error('Failed to load alert queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [priorityFilter, statusFilter, sortBy, sortOrder]);

  const handleOpenExplanation = async (alertId: string) => {
    try {
      setExplanationAlertId(alertId);
      const res = await apiService.getAlertPriorityExplanation(alertId);
      setExplanationData(res);
    } catch (err) {
      console.error('Failed to fetch priority explanation', err);
    }
  };

  const handleTriageSubmit = async () => {
    if (!triageAlertId) return;
    try {
      await apiService.triageAlert(triageAlertId, {
        new_status: selectedTriageStatus,
        notes: triageNotes,
      });
      setTriageAlertId(null);
      setTriageNotes('');
      fetchAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to triage alert');
    }
  };

  const handleAssignSubmit = async () => {
    if (!assignAlertId) return;
    try {
      await apiService.assignAlert(assignAlertId, {
        assigned_to: selectedAssignee,
      });
      setAssignAlertId(null);
      fetchAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to assign alert');
    }
  };

  const handleBulkAssign = async () => {
    if (selectedAlerts.length === 0) return;
    try {
      await apiService.bulkAssignAlerts({
        alert_ids: selectedAlerts,
        assigned_to: selectedAssignee,
      });
      setSelectedAlerts([]);
      fetchAlerts();
    } catch (err) {
      console.error('Failed bulk assign', err);
    }
  };

  const handleBulkClose = async () => {
    if (selectedAlerts.length === 0) return;
    try {
      await apiService.bulkTriageAlerts({
        alert_ids: selectedAlerts,
        new_status: 'CLOSED',
        notes: 'Bulk resolved from queue',
      });
      setSelectedAlerts([]);
      fetchAlerts();
    } catch (err) {
      console.error('Failed bulk close', err);
    }
  };

  const getPriorityBadge = (level: PriorityLevel, score: number) => {
    switch (level) {
      case 'P0_CRITICAL':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse">
            P0 CRITICAL ({score.toFixed(0)})
          </span>
        );
      case 'P1_HIGH':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40">
            P1 HIGH ({score.toFixed(0)})
          </span>
        );
      case 'P2_MEDIUM':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
            P2 MED ({score.toFixed(0)})
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            P3 LOW ({score.toFixed(0)})
          </span>
        );
    }
  };

  const getSLABadge = (status: SLAStatus, timeRemaining: number) => {
    switch (status) {
      case 'BREACHED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-950 text-rose-400 border border-rose-800 animate-pulse flex items-center gap-1">
            <Clock className="h-3 w-3" /> BREACHED
          </span>
        );
      case 'AT_RISK':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950 text-amber-300 border border-amber-700 flex items-center gap-1">
            <Clock className="h-3 w-3" /> {timeRemaining.toFixed(0)}m left
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
            RESOLVED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
            <Clock className="h-3 w-3" /> {timeRemaining > 60 ? `${(timeRemaining / 60).toFixed(1)}h` : `${timeRemaining.toFixed(0)}m`}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Investigator Alert Queue</h1>
          <p className="text-sm text-slate-400">
            Real-time prioritized alert queue with deterministic risk scoring and dynamic SLA tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Filter & Action Toolbar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search alert ID or account..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchAlerts()}
              className="pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-56"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Priorities</option>
            <option value="P0_CRITICAL">P0 Critical</option>
            <option value="P1_HIGH">P1 High</option>
            <option value="P2_MEDIUM">P2 Medium</option>
            <option value="P3_LOW">P3 Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Statuses</option>
            <option value="NEW">NEW</option>
            <option value="TRIAGED">TRIAGED</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="ESCALATED">ESCALATED</option>
            <option value="CONFIRMED_FRAUD">CONFIRMED FRAUD</option>
            <option value="FALSE_POSITIVE">FALSE POSITIVE</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </div>

        {/* Bulk Action controls */}
        {selectedAlerts.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-cyan-400 font-semibold">{selectedAlerts.length} selected</span>
            <button
              onClick={handleBulkAssign}
              className="px-2.5 py-1.5 bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 rounded-lg text-xs font-semibold hover:bg-cyan-600/30"
            >
              Assign to Me
            </button>
            <button
              onClick={handleBulkClose}
              className="px-2.5 py-1.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-700"
            >
              Close Selected
            </button>
          </div>
        )}
      </div>

      {/* Queue Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="p-3.5 w-8">
                  <input
                    type="checkbox"
                    checked={selectedAlerts.length === alerts.length && alerts.length > 0}
                    onChange={(e) =>
                      setSelectedAlerts(e.target.checked ? alerts.map((a) => a.alert_id) : [])
                    }
                    className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                </th>
                <th className="p-3.5">Priority</th>
                <th className="p-3.5">SLA Countdown</th>
                <th className="p-3.5">Alert & Pattern</th>
                <th className="p-3.5">Primary Entity</th>
                <th className="p-3.5">Financial Impact</th>
                <th className="p-3.5">Triage Status</th>
                <th className="p-3.5">Assignee</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-slate-500">
                    Loading prioritized alert queue...
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-slate-500">
                    No alerts match active filters.
                  </td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.alert_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5">
                      <input
                        type="checkbox"
                        checked={selectedAlerts.includes(a.alert_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAlerts([...selectedAlerts, a.alert_id]);
                          } else {
                            setSelectedAlerts(selectedAlerts.filter((id) => id !== a.alert_id));
                          }
                        }}
                        className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0"
                      />
                    </td>
                    <td className="p-3.5">
                      <button
                        onClick={() => handleOpenExplanation(a.alert_id)}
                        className="text-left group"
                        title="Click to view explainable risk factors"
                      >
                        {getPriorityBadge(a.priority_level, a.priority_score)}
                      </button>
                    </td>
                    <td className="p-3.5">{getSLABadge(a.sla_status, a.time_remaining_minutes)}</td>
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-200">{a.detection_type}</div>
                      <div className="text-[11px] text-slate-500 font-mono truncate max-w-xs">{a.alert_id}</div>
                    </td>
                    <td className="p-3.5">
                      <button
                        onClick={() => onSelectAccount && onSelectAccount(a.primary_account)}
                        className="font-mono text-cyan-400 hover:underline font-semibold"
                      >
                        {a.primary_account}
                      </button>
                      {a.risk_score !== undefined && (
                        <div className="text-[10px] text-slate-500">Risk: {a.risk_score?.toFixed(1)}/100</div>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-slate-200">
                      ${(a.total_amount || 0).toLocaleString()}
                    </td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {a.triage_status}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-400">
                      {a.assigned_investigator ? (
                        <span className="text-cyan-400 font-medium">{a.assigned_investigator}</span>
                      ) : (
                        <span className="text-slate-600 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="p-3.5 text-right space-x-2">
                      <button
                        onClick={() => {
                          setTriageAlertId(a.alert_id);
                          setSelectedTriageStatus(a.triage_status);
                        }}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 transition-colors"
                        title="Triage State Transition"
                      >
                        <ShieldCheck className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          setAssignAlertId(a.alert_id);
                          setSelectedAssignee(a.assigned_investigator || 'alice_investigator');
                        }}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 transition-colors"
                        title="Assign Investigator"
                      >
                        <UserCheck className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Priority Explainability Modal */}
      {explanationAlertId && explanationData && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-cyan-400" />
                Priority Score Breakdown
              </h3>
              <button
                onClick={() => {
                  setExplanationAlertId(null);
                  setExplanationData(null);
                }}
                className="text-slate-500 hover:text-slate-300 text-sm"
              >
                ✕
              </button>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/60 border border-slate-700">
              <div>
                <span className="text-xs text-slate-400 uppercase">Composite Priority</span>
                <div className="text-xl font-bold text-cyan-400">{explanationData.priority_score.toFixed(1)} / 100</div>
              </div>
              <div>{getPriorityBadge(explanationData.priority_level, explanationData.priority_score)}</div>
            </div>

            <div className="space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Contributing Signals</span>
              {explanationData.factors.map((f, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{f.factor_name} (Weight: {(f.weight * 100).toFixed(0)}%)</span>
                    <span className="font-mono text-cyan-400 font-bold">+{f.contribution.toFixed(1)} pts</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, f.raw_value)}%` }}></div>
                  </div>
                  <p className="text-[11px] text-slate-400">{f.evidence}</p>
                </div>
              ))}
            </div>

            <p className="text-xs text-slate-400 italic bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              {explanationData.summary}
            </p>
          </div>
        </div>
      )}

      {/* Triage Modal */}
      {triageAlertId && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-cyan-400" />
              Triage Alert: {triageAlertId}
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Triage State</label>
                <select
                  value={selectedTriageStatus}
                  onChange={(e) => setSelectedTriageStatus(e.target.value as TriageStatus)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="TRIAGED">TRIAGED</option>
                  <option value="INVESTIGATING">INVESTIGATING</option>
                  <option value="ESCALATED">ESCALATED</option>
                  <option value="CONFIRMED_FRAUD">CONFIRMED FRAUD</option>
                  <option value="FALSE_POSITIVE">FALSE POSITIVE</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Investigative Notes</label>
                <textarea
                  rows={3}
                  value={triageNotes}
                  onChange={(e) => setTriageNotes(e.target.value)}
                  placeholder="Provide justification or notes for this state transition..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setTriageAlertId(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-400 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleTriageSubmit}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 text-xs font-semibold text-white hover:bg-cyan-500"
              >
                Apply Transition
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assignment Modal */}
      {assignAlertId && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-cyan-400" />
              Assign Alert Investigator
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Select Investigator</label>
              <select
                value={selectedAssignee}
                onChange={(e) => setSelectedAssignee(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="alice_investigator">alice_investigator (Investigator)</option>
                <option value="bob_lead_investigator">bob_lead_investigator (Lead)</option>
                <option value="charlie_senior_analyst">charlie_senior_analyst (Senior)</option>
                <option value="admin">admin (Admin)</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setAssignAlertId(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-400 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAssignSubmit}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 text-xs font-semibold text-white hover:bg-cyan-500"
              >
                Confirm Assignment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
