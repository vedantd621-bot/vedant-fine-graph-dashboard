import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Plus,
  Search,
  Filter,
  Clock,
  User,
  AlertTriangle,
  FileText,
  Paperclip,
  CheckCircle,
  XCircle,
  ArrowRight,
  Send,
  Lock,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import {
  CasePriority,
  CaseStatus,
  InvestigationCase,
  InvestigationCaseSummary,
} from '../types';
import { TimelineView } from '../components/investigation/TimelineView';

interface CasesPageProps {
  onSelectAccount: (accountId: string) => void;
  onSelectAlert: (alertId: string) => void;
}

export const CasesPage: React.FC<CasesPageProps> = ({
  onSelectAccount,
  onSelectAlert,
}) => {
  const { hasRole, user } = useAuth();
  const isReadOnly = !hasRole('INVESTIGATOR');

  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected Case Detail
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseDetail, setCaseDetail] = useState<InvestigationCase | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [newNoteContent, setNewNoteContent] = useState<string>('');

  // New Case Modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newCaseTitle, setNewCaseTitle] = useState<string>('');
  const [newCaseDesc, setNewCaseDesc] = useState<string>('');
  const [newCasePriority, setNewCasePriority] = useState<CasePriority>('HIGH');
  const [newCaseAlerts, setNewCaseAlerts] = useState<string>('');
  const [newCaseAccounts, setNewCaseAccounts] = useState<string>('');

  const loadCases = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.listCases({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        search: searchQuery || undefined,
      });
      setCases(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load investigation cases.');
    } finally {
      setLoading(false);
    }
  };

  const loadCaseDetail = async (id: string) => {
    try {
      setDetailLoading(true);
      const detail = await apiClient.getCaseDetail(id);
      setCaseDetail(detail);
      setSelectedCaseId(id);
    } catch (err: any) {
      console.error('Failed to load case detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, priorityFilter]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseTitle.trim() || !newCaseDesc.trim()) return;

    try {
      const created = await apiClient.createCase({
        title: newCaseTitle.trim(),
        description: newCaseDesc.trim(),
        priority: newCasePriority,
        linked_alerts: newCaseAlerts ? newCaseAlerts.split(',').map((s) => s.trim()) : [],
        linked_accounts: newCaseAccounts ? newCaseAccounts.split(',').map((s) => s.trim()) : [],
      });
      setShowCreateModal(false);
      setNewCaseTitle('');
      setNewCaseDesc('');
      setNewCaseAlerts('');
      setNewCaseAccounts('');
      await loadCases();
      loadCaseDetail(created.case_id);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to create case');
    }
  };

  const handleStatusChange = async (newStatus: CaseStatus) => {
    if (!selectedCaseId) return;
    try {
      const updated = await apiClient.updateCase(selectedCaseId, { status: newStatus });
      setCaseDetail(updated);
      loadCases();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Status transition rejected');
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCaseId || !newNoteContent.trim()) return;

    try {
      await apiClient.addCaseNote(selectedCaseId, newNoteContent.trim());
      setNewNoteContent('');
      loadCaseDetail(selectedCaseId);
      loadCases();
    } catch (err: any) {
      alert('Failed to post note');
    }
  };

  const getPriorityBadge = (prio: CasePriority) => {
    switch (prio) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'MEDIUM':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getStatusBadge = (st: CaseStatus) => {
    switch (st) {
      case 'OPEN':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'IN_PROGRESS':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'ESCALATED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'RESOLVED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'CLOSED':
        return 'bg-slate-800 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-cyan-400" />
            Fraud Investigation Cases
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage end-to-end case workflows, notes, cryptographic evidence, and linked syndicate alerts.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          disabled={isReadOnly}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-colors ${
            isReadOnly
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
              : 'bg-cyan-600 hover:bg-cyan-500 text-slate-950 shadow-sm'
          }`}
          title={isReadOnly ? 'Requires INVESTIGATOR role' : 'Open new investigation case'}
        >
          {isReadOnly ? <Lock className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          New Investigation Case
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="h-4 w-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by case ID, title, or account..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadCases()}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="ESCALATED">Escalated</option>
          <option value="RESOLVED">Resolved</option>
          <option value="CLOSED">Closed</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Priorities</option>
          <option value="CRITICAL">Critical Priority</option>
          <option value="HIGH">High Priority</option>
          <option value="MEDIUM">Medium Priority</option>
          <option value="LOW">Low Priority</option>
        </select>
      </div>

      {/* Main Layout: List + Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Cases List */}
        <div className={selectedCaseId ? 'lg:col-span-5 space-y-3' : 'lg:col-span-12 space-y-3'}>
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading investigation cases...</div>
          ) : cases.length === 0 ? (
            <div className="p-8 text-center rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
              No cases match the selected filters.
            </div>
          ) : (
            cases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => loadCaseDetail(c.case_id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2.5 ${
                  selectedCaseId === c.case_id
                    ? 'bg-slate-850 border-cyan-500 shadow-md shadow-cyan-500/5'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-400">{c.case_id}</span>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${getPriorityBadge(c.priority)}`}>
                      {c.priority}
                    </span>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${getStatusBadge(c.status)}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="font-semibold text-xs text-slate-100 line-clamp-1">{c.title}</div>

                <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3 text-slate-500" />
                    {c.assigned_investigator || 'Unassigned'}
                  </span>
                  <div className="flex items-center gap-3">
                    <span>{c.alerts_count} Alerts</span>
                    <span>{c.evidence_count} Evidence</span>
                    <span>{c.notes_count} Notes</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Case Detail Workspace */}
        {selectedCaseId && caseDetail && (
          <div className="lg:col-span-7 p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-6 shadow-sm">
            {/* Detail Header */}
            <div className="space-y-3 pb-4 border-b border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-cyan-400">{caseDetail.case_id}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded border ${getPriorityBadge(caseDetail.priority)}`}>
                    {caseDetail.priority} PRIORITY
                  </span>
                  <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded border ${getStatusBadge(caseDetail.status)}`}>
                    {caseDetail.status.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <h2 className="text-base font-bold text-slate-100">{caseDetail.title}</h2>
              <p className="text-xs text-slate-300 leading-relaxed">{caseDetail.description}</p>

              {/* Status Transition Action Buttons */}
              {!isReadOnly && (
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <span className="text-[11px] font-bold text-slate-400 uppercase mr-1">Lifecycle Action:</span>
                  {caseDetail.status === 'OPEN' && (
                    <button
                      onClick={() => handleStatusChange('IN_PROGRESS')}
                      className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-slate-100 font-bold text-[11px]"
                    >
                      Start Investigation
                    </button>
                  )}
                  {caseDetail.status === 'IN_PROGRESS' && (
                    <>
                      <button
                        onClick={() => handleStatusChange('ESCALATED')}
                        className="px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-slate-100 font-bold text-[11px]"
                      >
                        Escalate Case
                      </button>
                      <button
                        onClick={() => handleStatusChange('RESOLVED')}
                        className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-100 font-bold text-[11px]"
                      >
                        Resolve Case
                      </button>
                    </>
                  )}
                  {caseDetail.status === 'ESCALATED' && (
                    <button
                      onClick={() => handleStatusChange('RESOLVED')}
                      className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-100 font-bold text-[11px]"
                    >
                      Resolve Case
                    </button>
                  )}
                  {caseDetail.status === 'RESOLVED' && (
                    <button
                      onClick={() => handleStatusChange('CLOSED')}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-[11px]"
                    >
                      Close Case
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Linked Entities */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-2">
                <span className="text-xs font-bold text-slate-300 block">Linked Accounts ({caseDetail.linked_accounts.length})</span>
                <div className="flex flex-wrap gap-1.5">
                  {caseDetail.linked_accounts.map((accId) => (
                    <button
                      key={accId}
                      onClick={() => onSelectAccount(accId)}
                      className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-500 text-cyan-300 font-mono text-xs"
                    >
                      {accId}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-2">
                <span className="text-xs font-bold text-slate-300 block">Linked Alerts ({caseDetail.linked_alerts.length})</span>
                <div className="flex flex-wrap gap-1.5">
                  {caseDetail.linked_alerts.map((altId) => (
                    <button
                      key={altId}
                      onClick={() => onSelectAlert(altId)}
                      className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 hover:border-cyan-500 text-amber-300 font-mono text-xs"
                    >
                      {altId}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Cryptographic Evidence Registry */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Paperclip className="h-4 w-4 text-purple-400" />
                Attached Forensic Evidence ({caseDetail.evidence.length})
              </h3>
              {caseDetail.evidence.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-800/40 text-center text-xs text-slate-500">
                  No forensic evidence registered yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {caseDetail.evidence.map((evd) => (
                    <div key={evd.evidence_id} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-200">{evd.title}</span>
                        <span className="text-[10px] font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">
                          {evd.type}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">{evd.description}</p>
                      {evd.integrity_hash && (
                        <div className="text-[10px] font-mono text-slate-500 pt-1">
                          SHA-256 Hash: {evd.integrity_hash.slice(0, 24)}...
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Notes Thread */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                Investigator Note Feed ({caseDetail.notes.length})
              </h3>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {caseDetail.notes.map((n) => (
                  <div key={n.note_id} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-cyan-400">{n.author_name}</span>
                      <span className="text-slate-500 font-mono">{new Date(n.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-xs text-slate-200">{n.content}</p>
                  </div>
                ))}
              </div>

              {!isReadOnly && (
                <form onSubmit={handleAddNote} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add an investigation finding or note..."
                    value={newNoteContent}
                    onChange={(e) => setNewNoteContent(e.target.value)}
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    type="submit"
                    className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5"
                  >
                    <Send className="h-3.5 w-3.5" /> Post
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal: Create Case */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-xl">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-cyan-400" />
              Open Investigation Case
            </h2>

            <form onSubmit={handleCreateCase} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Case Title</label>
                <input
                  type="text"
                  placeholder="e.g. Syndicate Circular Wash Trading Network"
                  value={newCaseTitle}
                  onChange={(e) => setNewCaseTitle(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Priority</label>
                <select
                  value={newCasePriority}
                  onChange={(e) => setNewCasePriority(e.target.value as CasePriority)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Description & Findings</label>
                <textarea
                  rows={3}
                  placeholder="Summary of anomalous graph patterns and accounts under review..."
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Initial Accounts (Comma separated)</label>
                <input
                  type="text"
                  placeholder="A001, A002, A003"
                  value={newCaseAccounts}
                  onChange={(e) => setNewCaseAccounts(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
                >
                  Create Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
