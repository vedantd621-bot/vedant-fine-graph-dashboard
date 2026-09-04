import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertCircle,
  Clock,
  CheckCircle2,
  Users,
  Compass,
  ArrowRight,
  TrendingUp,
  Activity,
  Layers,
} from 'lucide-react';
import { apiService } from '../api/client';
import {
  PrioritizedAlert,
  InvestigatorWorkload,
  SLASummary,
  InvestigationCaseSummary,
} from '../types';

interface InvestigationOperationsPageProps {
  onSelectAlert?: (alertId: string) => void;
  onSelectAccount?: (accountId: string) => void;
  onNavigate?: (tab: string) => void;
}

export const InvestigationOperationsPage: React.FC<InvestigationOperationsPageProps> = ({
  onSelectAlert,
  onSelectAccount,
  onNavigate,
}) => {
  const [myQueue, setMyQueue] = useState<PrioritizedAlert[]>([]);
  const [criticalAlerts, setCriticalAlerts] = useState<PrioritizedAlert[]>([]);
  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [workloads, setWorkloads] = useState<InvestigatorWorkload[]>([]);
  const [slaSummary, setSlaSummary] = useState<SLASummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadOpsData = async () => {
      try {
        setLoading(true);
        const [queueRes, critRes, caseRes, wlRes, slaRes] = await Promise.all([
          apiService.getInvestigatorQueue({ page_size: 10 }),
          apiService.listPrioritizedAlerts({ priority: 'P0_CRITICAL', page_size: 5 }),
          apiService.listCases({ page_size: 5 }),
          apiService.getInvestigatorWorkload(),
          apiService.getSLASummary(),
        ]);

        if (queueRes && queueRes.data) setMyQueue(queueRes.data);
        if (critRes && critRes.data) setCriticalAlerts(critRes.data);
        if (caseRes && caseRes.data) setCases(caseRes.data);
        if (wlRes && wlRes.investigators) setWorkloads(wlRes.investigators);
        if (slaRes) setSlaSummary(slaRes);
      } catch (err) {
        console.error('Failed to load investigator operations workstation', err);
      } finally {
        setLoading(false);
      }
    };
    loadOpsData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Investigator Operations Workstation</h1>
        <p className="text-sm text-slate-400">
          Personal triage queue, active investigations, SLA countdowns, and real-time operations activity.
        </p>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">My Active Queue</span>
          <div className="text-2xl font-bold text-cyan-400">{myQueue.length}</div>
          <span className="text-[11px] text-slate-500">Assigned alerts in triage</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Critical P0/P1 Alerts</span>
          <div className="text-2xl font-bold text-rose-400">{criticalAlerts.length}</div>
          <span className="text-[11px] text-rose-500/80">Immediate review required</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Open Cases</span>
          <div className="text-2xl font-bold text-amber-400">{cases.length}</div>
          <span className="text-[11px] text-slate-500">Active investigation dossiers</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">SLA Compliance</span>
          <div className="text-2xl font-bold text-emerald-400">
            {slaSummary ? `${slaSummary.compliance_rate.toFixed(0)}%` : '100%'}
          </div>
          <span className="text-[11px] text-slate-500">
            {slaSummary ? `${slaSummary.breached_count} breached alerts` : '0 breached'}
          </span>
        </div>
      </div>

      {/* Main Dual Work Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: My Queue & Critical Alerts */}
        <div className="lg:col-span-2 space-y-6">
          {/* My Queue Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Clock className="h-4 w-4 text-cyan-400" />
                Assigned Alerts Queue
              </h2>
              {onNavigate && (
                <button
                  onClick={() => onNavigate('alert-queue')}
                  className="text-xs text-cyan-400 hover:underline flex items-center gap-1"
                >
                  View Full Queue <ArrowRight className="h-3 w-3" />
                </button>
              )}
            </div>

            <div className="space-y-2.5">
              {loading ? (
                <div className="p-6 text-center text-xs text-slate-500">Loading queue...</div>
              ) : myQueue.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">No alerts assigned to your queue.</div>
              ) : (
                myQueue.map((a) => (
                  <div
                    key={a.alert_id}
                    className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 flex items-center justify-between hover:bg-slate-800/70 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-slate-200">{a.detection_type}</span>
                        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
                          {a.priority_level}
                        </span>
                        <span className="text-[10px] text-slate-400">{a.triage_status}</span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-3">
                        <span>Account: <button onClick={() => onSelectAccount && onSelectAccount(a.primary_account)} className="font-mono text-slate-200 hover:underline">{a.primary_account}</button></span>
                        <span>Exposure: <span className="font-mono text-slate-200">${(a.total_amount || 0).toLocaleString()}</span></span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[11px] font-bold text-amber-400 flex items-center gap-1 justify-end">
                        <Clock className="h-3 w-3" /> {a.time_remaining_minutes.toFixed(0)}m SLA
                      </div>
                      <span className="text-[10px] text-slate-500">{new Date(a.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Critical Alerts Stream */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-rose-400" />
                Critical Priority Stream (P0)
              </h2>
            </div>

            <div className="space-y-2.5">
              {criticalAlerts.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500">No active P0 critical alerts.</div>
              ) : (
                criticalAlerts.map((a) => (
                  <div
                    key={a.alert_id}
                    className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/40 flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-rose-300">{a.detection_type}</span>
                        <span className="text-[10px] font-bold text-rose-400 bg-rose-900/40 px-1.5 py-0.5 rounded">
                          SCORE {a.priority_score.toFixed(0)}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300">{a.description}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono font-bold text-rose-400">
                        ${(a.total_amount || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Active Cases & Team Workload */}
        <div className="space-y-6">
          {/* Active Cases */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-400" />
                Investigation Cases
              </h2>
              {onNavigate && (
                <button
                  onClick={() => onNavigate('cases')}
                  className="text-xs text-cyan-400 hover:underline"
                >
                  All Cases
                </button>
              )}
            </div>

            <div className="space-y-2.5">
              {cases.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500">No active cases.</div>
              ) : (
                cases.map((c) => (
                  <div key={c.case_id} className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-200 truncate">{c.title}</span>
                      <span className="text-[10px] text-amber-400 font-bold">{c.priority}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>{c.status}</span>
                      <span>{c.assigned_investigator || 'Unassigned'}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Team Workload Analytics */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Users className="h-4 w-4 text-cyan-400" />
                Investigator Capacity
              </h2>
            </div>

            <div className="space-y-3">
              {workloads.map((w) => (
                <div key={w.investigator_id} className="p-3 rounded-lg bg-slate-800/30 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{w.username}</span>
                    <span className="text-cyan-400 font-mono font-bold">{w.assigned_alerts} active</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-400 text-center">
                    <div className="bg-slate-800 p-1 rounded">
                      <span className="block text-slate-200 font-bold">{w.open_cases}</span>
                      <span>Cases</span>
                    </div>
                    <div className="bg-slate-800 p-1 rounded">
                      <span className="block text-rose-400 font-bold">{w.critical_alerts}</span>
                      <span>Critical</span>
                    </div>
                    <div className="bg-slate-800 p-1 rounded">
                      <span className="block text-emerald-400 font-bold">{w.alerts_resolved}</span>
                      <span>Resolved</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
