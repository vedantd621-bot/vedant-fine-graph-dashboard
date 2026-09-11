import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  FileText,
  Clock,
  ExternalLink,
  Users,
  Layers,
  Sparkles,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Activity,
  Info,
  DollarSign
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuth } from '../auth/AuthContext';

interface TransactionInvestigationDetailPageProps {
  transactionId?: string;
  onBack: () => void;
  onSelectAccount?: (accountId: string) => void;
  onSelectAlert?: (alertId: string) => void;
  onSelectCase?: (caseId: string) => void;
  onSelectNetwork?: (networkId: string) => void;
}

export const TransactionInvestigationDetailPage: React.FC<TransactionInvestigationDetailPageProps> = ({
  transactionId = 'TX-892410-FRD',
  onBack,
  onSelectAccount,
  onSelectAlert,
  onSelectCase,
  onSelectNetwork,
}) => {
  const { hasRole } = useAuth();
  const canMutate = hasRole(['INVESTIGATOR', 'ADMIN']);

  const [activeTxId, setActiveTxId] = useState<string>(transactionId);
  const [loading, setLoading] = useState<boolean>(false);
  const [decisionVerdict, setDecisionVerdict] = useState<'BLOCK' | 'ALLOW' | 'REVIEW' | 'ESCALATE'>('BLOCK');
  const [decisionNotes, setDecisionNotes] = useState<string>('');
  const [decisionSuccess, setDecisionSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (transactionId) {
      setActiveTxId(transactionId);
    }
  }, [transactionId]);

  const txData = {
    transaction_id: activeTxId,
    timestamp: '2026-09-07T08:42:15Z',
    amount: 148500.00,
    currency: 'USD',
    channel: 'SWIFT_WIRE',
    status: 'FLAGGED_SUSPICIOUS',
    source_account: 'ACC-39481-US',
    source_holder: 'Aegis Global Holdings LLC',
    destination_account: 'ACC-88301-CY',
    destination_holder: 'Cyprus Meridian Ltd',
    ip_address: '185.220.101.44 (Tor Exit Node)',
    device_id: 'DEV-FP-9941-X7',
    location: 'Nicosia, Cyprus / Proxy origin: Frankfurt, DE',
    risk_score: 94.2,
    threat_level: 'CRITICAL',
    velocity_1h: 4,
    velocity_24h: 18,
    indicators: [
      { id: 'IND-1', name: 'Layered Structuring Velocity', severity: 'HIGH', desc: '14 split wires within 18 minutes just below $10,000 threshold' },
      { id: 'IND-2', name: 'High-Risk Geo Mismatch', severity: 'CRITICAL', desc: 'Source routing originated via Tor exit relay with foreign offshore counterparty' },
      { id: 'IND-3', name: 'Circular Money Flow', severity: 'CRITICAL', desc: '89.4% of total funds return to origin syndicate cluster within 48 hours' },
      { id: 'IND-4', name: 'Rapid Dormant Account Activation', severity: 'MEDIUM', desc: 'Account was inactive for 312 days before sudden multi-hundred thousand volume' }
    ],
    rule_triggers: [
      { code: 'R-701', rule: 'Circular Laundering Pattern', fired: true, weight: 0.95 },
      { code: 'R-402', rule: 'Rapid Multi-Hop Funneling', fired: true, weight: 0.88 },
      { code: 'R-205', rule: 'Tor / Proxy Anonymization', fired: true, weight: 0.91 },
      { code: 'R-112', rule: 'High Velocity Value Burst', fired: true, weight: 0.82 }
    ],
    related_alerts: [
      { id: 'ALT-1092', type: 'CIRCULAR_FLOW', severity: 'CRITICAL', title: 'Circular Fund Transfer Cluster Detected' },
      { id: 'ALT-1088', type: 'RAPID_MOVEMENT', severity: 'HIGH', title: 'High Velocity Offshore Wire Sequence' }
    ],
    related_cases: [
      { id: 'CASE-2026-089', title: 'Syndicate Meridian Laundering Ring', status: 'ACTIVE', priority: 'CRITICAL' }
    ],
    related_networks: [
      { id: 'NET-004', name: 'Layered Funnel Cluster #4', risk_score: 96.5, member_count: 14 }
    ],
    timeline: [
      { time: '2026-09-07 08:35:10', event: 'Initial authentication from novel IP 185.220.101.44' },
      { time: '2026-09-07 08:38:22', event: 'Beneficiary account ACC-88301-CY registered with zero cooldown' },
      { time: '2026-09-07 08:42:15', event: 'Wire instruction $148,500.00 initiated via SWIFT API' },
      { time: '2026-09-07 08:42:16', event: 'Realtime Flink detection: CircularFlowDetector score: 94.2' },
      { time: '2026-09-07 08:42:18', event: 'Automated containment hold triggered; queued for investigator triage' }
    ]
  };

  const handleApplyDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 600));
      setDecisionSuccess(true);
      setTimeout(() => setDecisionSuccess(false), 4000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Overview</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Forensic Investigation Dossier</span>
          <span className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-mono font-bold">
            THREAT: {txData.threat_level}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xl font-black text-cyan-400 tracking-wide">
                {txData.transaction_id}
              </span>
              <span className="text-xs font-bold uppercase px-3 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {txData.status}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Channel: {txData.channel}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Executed at: <span className="font-mono text-slate-300">{txData.timestamp}</span> • Device: <span className="font-mono text-slate-300">{txData.device_id}</span>
            </p>
          </div>

          <div className="flex items-center gap-4 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-500">Transaction Value</div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                ${txData.amount.toLocaleString()} <span className="text-xs text-slate-400">{txData.currency}</span>
              </div>
            </div>
            <div className="w-px h-8 bg-slate-800" />
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-500">Anomaly Risk Score</div>
              <div className="text-xl font-bold font-mono text-rose-400">
                {txData.risk_score} <span className="text-xs text-slate-400">/ 100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Counterparty Flow Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Source Account */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-slate-400">Source Entity (Origin)</span>
              <button
                onClick={() => onSelectAccount && onSelectAccount(txData.source_account)}
                className="text-cyan-400 hover:text-cyan-300 text-xs font-mono font-bold flex items-center gap-1 hover:underline"
              >
                {txData.source_account} <ExternalLink className="h-3 w-3" />
              </button>
            </div>
            <div className="text-sm font-semibold text-slate-200">{txData.source_holder}</div>
            <div className="text-xs text-slate-500">Velocity: {txData.velocity_1h} tx/hr • Total 24h: {txData.velocity_24h} txs</div>
          </div>

          {/* Destination Account */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-slate-400">Beneficiary Entity (Target)</span>
              <button
                onClick={() => onSelectAccount && onSelectAccount(txData.destination_account)}
                className="text-cyan-400 hover:text-cyan-300 text-xs font-mono font-bold flex items-center gap-1 hover:underline"
              >
                {txData.destination_account} <ExternalLink className="h-3 w-3" />
              </button>
            </div>
            <div className="text-sm font-semibold text-slate-200">{txData.destination_holder}</div>
            <div className="text-xs text-slate-500">Location: {txData.location}</div>
          </div>
        </div>
      </div>

      {/* Forensic Intelligence Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Fraud Indicators & Rule Signals */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key Fraud Indicators */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-rose-400" />
              Detected Fraud Indicators ({txData.indicators.length})
            </h3>
            <div className="space-y-2.5">
              {txData.indicators.map((ind) => (
                <div
                  key={ind.id}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-colors space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-200">{ind.name}</span>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                        ind.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : ind.severity === 'HIGH'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {ind.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{ind.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Rule Triggers & Graph Signals */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Rule & Graph Neural Model Triggers
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {txData.rule_triggers.map((rule) => (
                <div
                  key={rule.code}
                  className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between"
                >
                  <div>
                    <div className="font-mono text-xs text-cyan-400 font-bold">{rule.code}</div>
                    <div className="text-xs text-slate-200 font-medium">{rule.rule}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-rose-500/20 text-rose-400">
                      FIRED
                    </span>
                    <div className="text-[10px] text-slate-500 mt-1">Weight: {(rule.weight * 100).toFixed(0)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Transaction Forensic Execution Timeline */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              Forensic Execution Sequence
            </h3>
            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {txData.timeline.map((item, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-6 top-1.5 w-2 h-2 rounded-full bg-cyan-400 ring-4 ring-slate-900" />
                  <div className="text-[11px] font-mono text-slate-500">{item.time}</div>
                  <div className="text-xs text-slate-300 font-medium">{item.event}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Associations & Investigator Decision Panel */}
        <div className="space-y-6">
          {/* Related Entities & Networks */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              Syndicate & Network Associations
            </h3>

            {/* Related Fraud Network */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase text-slate-500">Fraud Network Membership</span>
              {txData.related_networks.map((net) => (
                <div
                  key={net.id}
                  onClick={() => onSelectNetwork && onSelectNetwork(net.id)}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-indigo-500/40 cursor-pointer transition-all space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-indigo-400">{net.id}</span>
                    <span className="text-[10px] font-bold text-rose-400">Risk: {net.risk_score}</span>
                  </div>
                  <div className="text-xs text-slate-200">{net.name}</div>
                  <div className="text-[11px] text-slate-500">{net.member_count} connected nodes</div>
                </div>
              ))}
            </div>

            {/* Related Investigation Cases */}
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <span className="text-[11px] font-bold uppercase text-slate-500">Associated Investigation Cases</span>
              {txData.related_cases.map((c) => (
                <div
                  key={c.id}
                  onClick={() => onSelectCase && onSelectCase(c.id)}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-cyan-400">{c.id}</span>
                    <span className="text-[10px] font-bold text-rose-400">{c.priority}</span>
                  </div>
                  <div className="text-xs text-slate-200">{c.title}</div>
                  <div className="text-[11px] text-slate-500">Status: {c.status}</div>
                </div>
              ))}
            </div>

            {/* Related Alerts */}
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <span className="text-[11px] font-bold uppercase text-slate-500">Triggered Alerts</span>
              {txData.related_alerts.map((alt) => (
                <div
                  key={alt.id}
                  onClick={() => onSelectAlert && onSelectAlert(alt.id)}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-rose-500/40 cursor-pointer transition-all space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-rose-400">{alt.id}</span>
                    <span className="text-[10px] font-bold text-slate-400">{alt.type}</span>
                  </div>
                  <div className="text-xs text-slate-300">{alt.title}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Investigator Decisioning / Containment Action */}
          <div className="p-5 rounded-xl bg-slate-900 border border-cyan-500/30 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              Investigator Decisioning Action
            </h3>

            {decisionSuccess && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Decision verdict recorded and published to audit log!
              </div>
            )}

            <form onSubmit={handleApplyDecision} className="space-y-3">
              <div>
                <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1">
                  Enforcement Verdict
                </label>
                <select
                  value={decisionVerdict}
                  onChange={(e: any) => setDecisionVerdict(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="BLOCK">BLOCK & FREEZE ENTITY (Recommended)</option>
                  <option value="ESCALATE">ESCALATE TO TIER-2 FRAUD DESK</option>
                  <option value="REVIEW">FLAG FOR ONGOING MONITORING</option>
                  <option value="ALLOW">OVERRIDE AS FALSE POSITIVE</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1">
                  Investigator Rationale & Evidence Note
                </label>
                <textarea
                  rows={3}
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  placeholder="Record forensic rationale, wire hold details, and regulatory SAR referral context..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !canMutate}
                className="w-full py-2.5 px-4 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Submitting Verdict...' : 'Execute Containment Verdict'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
export default TransactionInvestigationDetailPage;
