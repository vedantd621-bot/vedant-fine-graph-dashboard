import React, { useEffect, useState } from 'react';
import {
  CaseChecklistItem,
  CorrelationGroup,
  InvestigationBrief,
  InvestigationRecommendation,
  InvestigationTask,
  RankedEvidenceItem,
  RelatedCase,
  UnifiedTimelineEvent,
  WorkflowState,
} from '../types';
import { apiService } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export const InvestigationIntelligencePage: React.FC = () => {
  const { user } = useAuth();
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-2026-001');
  const [brief, setBrief] = useState<InvestigationBrief | null>(null);
  const [evidence, setEvidence] = useState<RankedEvidenceItem[]>([]);
  const [tasks, setTasks] = useState<InvestigationTask[]>([]);
  const [checklist, setChecklist] = useState<CaseChecklistItem[]>([]);
  const [recommendations, setRecommendations] = useState<InvestigationRecommendation[]>([]);
  const [relatedCases, setRelatedCases] = useState<RelatedCase[]>([]);
  const [timeline, setTimeline] = useState<UnifiedTimelineEvent[]>([]);
  const [workflowState, setWorkflowState] = useState<WorkflowState>('INVESTIGATING');
  const [activeTab, setActiveTab] = useState<'brief' | 'evidence' | 'tasks' | 'timeline' | 'recommendations'>('brief');
  const [loading, setLoading] = useState<boolean>(true);
  const [newTaskTitle, setNewTaskTitle] = useState<string>('');
  const [newChecklistTitle, setNewChecklistTitle] = useState<string>('');

  const isInvestigator = user?.role === 'investigator' || user?.role === 'admin';

  const loadCaseData = async (caseId: string) => {
    try {
      setLoading(true);
      const [bRes, eRes, tRes, cRes, rRes, relRes, tlRes, stRes] = await Promise.all([
        apiService.getInvestigationBrief(caseId),
        apiService.getRankedEvidence(caseId),
        apiService.listInvestigationTasks({ case_id: caseId }),
        apiService.getCaseChecklist(caseId),
        apiService.getInvestigationRecommendations(caseId),
        apiService.discoverRelatedCases(caseId),
        apiService.getUnifiedTimeline(caseId, 25),
        apiService.getCaseWorkflowState(caseId),
      ]);
      setBrief(bRes.data);
      setEvidence(eRes.data);
      setTasks(tRes.data);
      setChecklist(cRes.data);
      setRecommendations(rRes.data);
      setRelatedCases(relRes.data);
      setTimeline(tlRes.data);
      setWorkflowState(stRes.data);
    } catch (err) {
      console.error('Failed to load investigation intelligence data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseData(selectedCaseId);
  }, [selectedCaseId]);

  const handleStateTransition = async (targetState: string) => {
    try {
      await apiService.transitionCaseWorkflowState(selectedCaseId, { to_state: targetState, notes: `Transitioned by ${user?.username}` });
      setWorkflowState(targetState as WorkflowState);
    } catch (err: any) {
      alert(`Transition failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleToggleChecklist = async (item: CaseChecklistItem) => {
    try {
      await apiService.updateCaseChecklistItem(selectedCaseId, item.item_id, { is_completed: !item.is_completed });
      setChecklist(checklist.map(c => c.item_id === item.item_id ? { ...c, is_completed: !c.is_completed } : c));
    } catch (err) {
      console.error('Failed to toggle checklist item:', err);
    }
  };

  const handleCreateTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      const res = await apiService.createInvestigationTask({
        case_id: selectedCaseId,
        title: newTaskTitle.trim(),
        description: 'Assigned investigator action item',
        priority: 'HIGH',
        assignee: user?.username || 'investigator',
      });
      setTasks([res.data, ...tasks]);
      setNewTaskTitle('');
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const handleAddChecklistItem = async () => {
    if (!newChecklistTitle.trim()) return;
    try {
      const res = await apiService.addCaseChecklistItem(selectedCaseId, { title: newChecklistTitle.trim() });
      setChecklist([...checklist, res.data]);
      setNewChecklistTitle('');
    } catch (err) {
      console.error('Failed to add checklist item:', err);
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    try {
      const res = await apiService.completeInvestigationTask(taskId);
      setTasks(tasks.map(t => t.task_id === taskId ? res.data : t));
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      {/* Header & Case Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              🧭
            </span>
            Investigation Intelligence & Automation Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated dossier synthesis, evidence ranking, task coordination, and deterministic next-step recommendations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none font-mono"
          >
            <option value="CASE-2026-001">CASE-2026-001 (Syndicate Circular Wash)</option>
            <option value="CASE-2026-002">CASE-2026-002 (Account Takeover Cluster)</option>
            <option value="CASE-2026-003">CASE-2026-003 (Money Mule Network)</option>
          </select>

          {isInvestigator && (
            <select
              value={workflowState}
              onChange={(e) => handleStateTransition(e.target.value)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg px-3 py-2.5 outline-none"
            >
              <option value="CREATED">State: CREATED</option>
              <option value="TRIAGED">State: TRIAGED</option>
              <option value="INVESTIGATING">State: INVESTIGATING</option>
              <option value="EVIDENCE_REVIEW">State: EVIDENCE REVIEW</option>
              <option value="DECISION_PENDING">State: DECISION PENDING</option>
              <option value="DECIDED">State: DECIDED</option>
              <option value="CLOSED">State: CLOSED</option>
            </select>
          )}
        </div>
      </div>

      {/* Priority & Exposure KPI Cards */}
      {brief && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Investigation Priority</div>
            <div className="text-3xl font-black text-rose-400 mt-1">
              {brief.priority_assessment.priority_score} <span className="text-xs font-normal text-slate-500">/ 100</span>
            </div>
            <div className="text-xs text-rose-400 font-semibold mt-1">Band: {brief.priority_assessment.priority_band}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Exposure</div>
            <div className="text-3xl font-bold text-emerald-400 mt-1">
              ${brief.financial_exposure.toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">Across 7 linked entities</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Workflow Lifecycle</div>
            <div className="text-2xl font-bold text-indigo-400 mt-1.5">{workflowState}</div>
            <div className="text-xs text-slate-500 mt-1">Procedural State Machine</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ranked Evidence</div>
            <div className="text-3xl font-bold text-amber-400 mt-1">{evidence.length} Items</div>
            <div className="text-xs text-slate-500 mt-1">{evidence.filter(e => e.strength === 'STRONG').length} Strong Provenance</div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('brief')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'brief' ? 'border-indigo-500 text-indigo-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Investigation Brief
        </button>
        <button
          onClick={() => setActiveTab('evidence')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'evidence' ? 'border-indigo-500 text-indigo-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Ranked Evidence Dossier ({evidence.length})
        </button>
        <button
          onClick={() => setActiveTab('tasks')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'tasks' ? 'border-indigo-500 text-indigo-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Tasks & Checklist ({tasks.length})
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'recommendations' ? 'border-indigo-500 text-indigo-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Advisory Recommendations ({recommendations.length})
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'timeline' ? 'border-indigo-500 text-indigo-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Unified Forensic Timeline
        </button>
      </div>

      {/* TAB 1: Investigation Brief */}
      {activeTab === 'brief' && brief && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>📄</span> Executive Dossier Summary
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">{brief.executive_summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-1">
                <span className="text-slate-400 font-semibold uppercase">Risk Profile</span>
                <p className="text-slate-200">{brief.risk_summary}</p>
              </div>
              <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-1">
                <span className="text-slate-400 font-semibold uppercase">Network Structure</span>
                <p className="text-slate-200">{brief.network_summary}</p>
              </div>
              <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-1">
                <span className="text-slate-400 font-semibold uppercase">Behavior Outliers</span>
                <p className="text-slate-200">{brief.behavior_summary}</p>
              </div>
            </div>
          </div>

          {/* Related Cases & Campaign Associations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center justify-between">
                <span>🔗 Related Investigation Cases</span>
                <span className="text-xs text-indigo-400 font-mono">{relatedCases.length} Discovered</span>
              </h3>
              <div className="space-y-2">
                {relatedCases.map((rc) => (
                  <div key={rc.case_id} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white">{rc.case_id}</span>
                      <span className="text-emerald-400 font-semibold">{(rc.relationship_score * 100).toFixed(0)}% Overlap</span>
                    </div>
                    <ul className="text-slate-400 space-y-0.5 mt-1">
                      {rc.relationship_reasons.map((r, i) => (
                        <li key={i}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">❓ Key Investigative Open Questions</h3>
              <div className="space-y-2">
                {brief.open_questions.map((q, i) => (
                  <div key={i} className="flex items-start gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs text-slate-300">
                    <span className="text-amber-400 font-bold">?</span>
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Ranked Evidence */}
      {activeTab === 'evidence' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3">
            {evidence.map((item) => (
              <div key={item.evidence_id} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {item.category}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded font-bold uppercase ${
                        item.strength === 'STRONG'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : item.strength === 'MODERATE'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {item.strength}
                    </span>
                    <span className="text-xs text-slate-400">Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">Source: {item.source}</span>
                </div>
                <h4 className="font-bold text-sm text-white">{item.title}</h4>
                <p className="text-xs text-slate-300">{item.description}</p>
                <div className="text-[11px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800/80">
                  <strong>Provenance:</strong> {item.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Tasks & Checklist */}
      {activeTab === 'tasks' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tasks Column */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>📋 Investigation Action Tasks</span>
              <span className="text-xs text-slate-400 font-mono">{tasks.length} Active</span>
            </h3>

            {isInvestigator && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="Assign new task..."
                  className="flex-grow bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none"
                />
                <button
                  onClick={handleCreateTask}
                  className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition"
                >
                  + Add Task
                </button>
              </div>
            )}

            <div className="space-y-3">
              {tasks.map((t) => (
                <div key={t.task_id} className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">{t.title}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        t.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{t.description}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Assignee: <strong className="text-slate-300">{t.assignee}</strong></span>
                    {isInvestigator && t.status !== 'COMPLETED' && (
                      <button
                        onClick={() => handleCompleteTask(t.task_id)}
                        className="text-emerald-400 hover:text-emerald-300 font-semibold"
                      >
                        ✓ Mark Complete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Checklist Column */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>☑️ Case Investigation Checklist</span>
              <span className="text-xs text-slate-400 font-mono">
                {checklist.filter(c => c.is_completed).length} / {checklist.length} Completed
              </span>
            </h3>

            {isInvestigator && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newChecklistTitle}
                  onChange={(e) => setNewChecklistTitle(e.target.value)}
                  placeholder="Add checklist item..."
                  className="flex-grow bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none"
                />
                <button
                  onClick={handleAddChecklistItem}
                  className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition"
                >
                  + Add Item
                </button>
              </div>
            )}

            <div className="space-y-2">
              {checklist.map((item) => (
                <div
                  key={item.item_id}
                  onClick={() => isInvestigator && handleToggleChecklist(item)}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition cursor-pointer ${
                    item.is_completed ? 'bg-slate-950/60 border-emerald-500/30' : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={item.is_completed}
                    onChange={() => {}}
                    className="rounded text-indigo-600 focus:ring-0"
                  />
                  <span className={`text-xs ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}`}>
                    {item.title}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Recommendations */}
      {activeTab === 'recommendations' && (
        <div className="space-y-3">
          {recommendations.map((rec) => (
            <div key={rec.recommendation_id} className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {rec.action_type}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    {rec.priority}
                  </span>
                </div>
                <span className="text-xs text-slate-400">Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
              </div>
              <h4 className="font-bold text-sm text-white">{rec.title}</h4>
              <p className="text-xs text-slate-300">{rec.reason}</p>
              <div className="pt-2">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Supporting Evidence:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {rec.supporting_evidence.map((e, idx) => (
                    <span key={idx} className="text-[10px] bg-slate-950 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 5: Unified Timeline */}
      {activeTab === 'timeline' && (
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
          <h3 className="text-base font-bold text-white">Chronological Forensic Event Stream</h3>
          <div className="space-y-3">
            {timeline.map((evt) => (
              <div key={evt.event_id} className="flex gap-4 items-start bg-slate-950 p-3.5 rounded-lg border border-slate-800">
                <div className="flex-shrink-0 w-24 text-center">
                  <span className="text-[10px] font-mono text-slate-400">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex-grow space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{evt.title}</span>
                    <span className="text-[10px] font-mono text-indigo-400 px-1.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                      {evt.source}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{evt.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default InvestigationIntelligencePage;
