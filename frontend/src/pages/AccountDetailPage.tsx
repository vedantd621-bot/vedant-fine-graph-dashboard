import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Snowflake,
  ShieldAlert,
  Users,
  Building,
  DollarSign,
  Activity,
  CheckCircle,
  ExternalLink,
  Sparkles,
  Layers,
  Clock,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  AccountDetail,
  AccountTransactionItem,
  EntityRiskProfile,
  GraphPayload,
  InvestigationTimelineEvent,
} from '../types';
import { InteractiveGraph } from '../components/graph/InteractiveGraph';
import { TimelineView } from '../components/investigation/TimelineView';
import { realtimeClient } from '../realtime/websocket';
import { GraphUpdatedData, RiskUpdatedData, TransactionCreatedData } from '../types/realtime';
import { useAuth } from '../auth/AuthContext';

interface AccountDetailPageProps {
  accountId: string;
  onBack: () => void;
  onSelectAccount: (accountId: string) => void;
}

export const AccountDetailPage: React.FC<AccountDetailPageProps> = ({
  accountId,
  onBack,
  onSelectAccount,
}) => {
  const { hasRole } = useAuth();
  const canFreeze = hasRole(['INVESTIGATOR', 'ADMIN']);

  const [account, setAccount] = useState<AccountDetail | null>(null);
  const [riskProfile, setRiskProfile] = useState<EntityRiskProfile | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<InvestigationTimelineEvent[]>([]);
  const [transactions, setTransactions] = useState<AccountTransactionItem[]>([]);
  const [graphData, setGraphData] = useState<GraphPayload | null>(null);
  const [graphDepth, setGraphDepth] = useState<number>(2);
  const [suspiciousOnly, setSuspiciousOnly] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [freezing, setFreezing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountData = async () => {
    try {
      setLoading(true);
      const [accRes, txRes, gRes, profRes, tlRes] = await Promise.all([
        apiClient.getAccountDetail(accountId),
        apiClient.getAccountTransactions(accountId, { page: 1, page_size: 20 }),
        suspiciousOnly
          ? apiClient.getSuspiciousNeighborhood(accountId, 60.0)
          : apiClient.getAccountGraph(accountId, graphDepth),
        apiClient.getEntityRiskProfile(accountId).catch(() => null),
        apiClient.getEntityTimeline(accountId).catch(() => ({ events: [] })),
      ]);
      setAccount(accRes);
      setTransactions(txRes.data);
      setGraphData(gRes);
      if (profRes) setRiskProfile(profRes);
      if (tlRes && tlRes.events) setTimelineEvents(tlRes.events);
    } catch (err: any) {
      setError(err.message || 'Failed to load account dossier.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccountData();
    realtimeClient.watchAccount(accountId);
  }, [accountId, graphDepth, suspiciousOnly]);

  useEffect(() => {
    const unsubRisk = realtimeClient.on('risk.updated', (evt) => {
      const data: RiskUpdatedData = evt.data;
      if (data.account_id === accountId) {
        setAccount((prev) =>
          prev
            ? {
                ...prev,
                risk_score: data.score,
                risk_level: data.risk_level,
                risk_reasons: data.reasons?.length ? data.reasons : prev.risk_reasons,
                calculated_at: data.calculated_at,
              }
            : prev
        );
      }
    });

    const unsubGraph = realtimeClient.on('graph.updated', async (evt) => {
      const data: GraphUpdatedData = evt.data;
      if (data.account_id === accountId || data.related_account_id === accountId) {
        try {
          const updatedGraph = suspiciousOnly
            ? await apiClient.getSuspiciousNeighborhood(accountId, 60.0)
            : await apiClient.getAccountGraph(accountId, graphDepth);
          setGraphData(updatedGraph);
        } catch (e) {
          console.debug('Failed to live-refresh graph:', e);
        }
      }
    });

    const unsubTx = realtimeClient.on('transaction.created', (evt) => {
      const data: TransactionCreatedData = evt.data;
      if (data.source_account === accountId || data.destination_account === accountId) {
        const isIncoming = data.destination_account === accountId;
        const newTxItem: AccountTransactionItem = {
          transaction_id: data.transaction_id,
          direction: isIncoming ? 'INCOMING' : 'OUTGOING',
          counterparty: isIncoming ? data.source_account : data.destination_account,
          amount: data.amount,
          currency: data.currency || 'USD',
          timestamp: data.timestamp,
          transaction_type: 'transfer',
          scenario_id: data.scenario_id,
          channel: data.channel,
        };
        setTransactions((prev) => [newTxItem, ...prev]);
      }
    });

    return () => {
      unsubRisk();
      unsubGraph();
      unsubTx();
    };
  }, [accountId, graphDepth, suspiciousOnly]);

  const handleToggleFreeze = async () => {
    if (!account) return;
    try {
      setFreezing(true);
      const res = await apiClient.freezeAccount(
        accountId,
        !account.is_frozen,
        'Simulated containment freeze from investigation dashboard'
      );
      setAccount({ ...account, is_frozen: res.is_frozen });
    } catch (err: any) {
      alert(`Freeze action failed: ${err.message}`);
    } finally {
      setFreezing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <span>Loading account dossier...</span>
      </div>
    );
  }

  if (error || !account) {
    return (
      <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
        <p>{error || 'Account not found.'}</p>
        <button onClick={onBack} className="mt-3 text-xs underline">
          Back to Accounts
        </button>
      </div>
    );
  }

  const isCrit = account.risk_level === 'CRITICAL';
  const isHigh = account.risk_level === 'HIGH';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Accounts
        </button>

        <button
          disabled={freezing || !canFreeze}
          onClick={handleToggleFreeze}
          title={!canFreeze ? 'Account containment requires Investigator or Admin role' : undefined}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-colors ${
            !canFreeze
              ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-60'
              : account.is_frozen
              ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30'
              : 'bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/30'
          }`}
        >
          <Snowflake className="h-4 w-4" />
          {account.is_frozen ? 'Unfreeze Account' : 'Simulate Account Freeze'}
          {!canFreeze && <span className="text-[10px] font-normal text-slate-500">(Read-Only)</span>}
        </button>
      </div>

      {/* Account Banner Dossier */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold font-mono text-slate-100">{account.account_id}</h2>
              <span
                className={`text-xs font-bold uppercase px-2.5 py-0.5 rounded border ${
                  isCrit
                    ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                    : isHigh
                    ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                    : 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                }`}
              >
                {account.risk_score.toFixed(1)}/100 · {account.risk_level} RISK
              </span>
              {account.is_frozen && (
                <span className="text-xs font-bold uppercase px-2.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center gap-1">
                  <Snowflake className="h-3 w-3" /> FROZEN
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5 text-cyan-400" />
                Owner: <span className="text-slate-200 font-medium">{account.owner_name || account.owner_id || 'Unknown'}</span>
              </span>
              <span className="flex items-center gap-1">
                <Building className="h-3.5 w-3.5 text-indigo-400" />
                Bank: <span className="text-slate-200 font-medium">{account.bank_name || account.bank_id || 'Apex Bank'}</span>
              </span>
              <span>Type: <span className="text-slate-200 font-medium">{account.account_type}</span></span>
            </div>
          </div>

          <div className="text-right text-xs text-slate-400 space-y-1">
            <div>Model Version: <span className="text-cyan-400 font-mono">{account.model_version}</span></div>
            <div>Evaluated: <span className="text-slate-200">{account.calculated_at ? new Date(account.calculated_at).toLocaleTimeString() : 'Real-time'}</span></div>
          </div>
        </div>

        {/* Graph Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span className="text-slate-400">PageRank Centrality</span>
            <div className="text-lg font-bold text-cyan-400 mt-1">{account.features.pagerank.toFixed(3)}</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span className="text-slate-400">Network Degree</span>
            <div className="text-lg font-bold text-slate-200 mt-1">
              {account.features.total_degree} <span className="text-xs text-slate-400 font-normal">(In {account.features.in_degree}, Out {account.features.out_degree})</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span className="text-slate-400">Louvain Community</span>
            <div className="text-lg font-bold text-indigo-400 mt-1">
              {account.features.louvain_community_id !== undefined ? `Group ${account.features.louvain_community_id}` : 'None'}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span className="text-slate-400">Total Transacted Volume</span>
            <div className="text-lg font-bold text-emerald-400 mt-1">
              ${account.features.total_volume.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Explainable Risk Factors Breakdown */}
        {riskProfile && riskProfile.major_risk_factors.length > 0 && (
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
              <Sparkles className="h-4 w-4" />
              Ranked Risk Factors & Topological Evidence
            </div>
            <div className="space-y-2 pt-1">
              {riskProfile.major_risk_factors.map((rf, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-start justify-between gap-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-200">{rf.factor_type.replace('_', ' ')}</span>
                      {rf.evidence_reference && (
                        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">
                          {rf.evidence_reference}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-400 text-[11px]">{rf.description}</p>
                  </div>
                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 shrink-0">
                    Weight: {rf.weight.toFixed(1)}x
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Interactive Subgraph Neighborhood */}
      {graphData && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              Interactive Subgraph Neighborhood ({account.account_id})
            </h3>
            <div className="flex items-center gap-3 text-xs">
              <button
                onClick={() => setSuspiciousOnly(!suspiciousOnly)}
                className={`px-2.5 py-1 rounded-lg border text-xs font-semibold transition-colors ${
                  suspiciousOnly
                    ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {suspiciousOnly ? 'Showing Suspicious Only' : 'Filter Suspicious'}
              </button>

              <div className="flex items-center gap-1">
                <span className="text-slate-400">Depth:</span>
                <button
                  onClick={() => setGraphDepth(1)}
                  className={`px-2 py-0.5 rounded ${graphDepth === 1 ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300'}`}
                >
                  1 Hop
                </button>
                <button
                  onClick={() => setGraphDepth(2)}
                  className={`px-2 py-0.5 rounded ${graphDepth === 2 ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300'}`}
                >
                  2 Hops
                </button>
              </div>
            </div>
          </div>
          <InteractiveGraph
            data={graphData}
            focalAccountId={account.account_id}
            onSelectNode={onSelectAccount}
            height={440}
          />
        </div>
      )}

      {/* Forensic Timeline */}
      {timelineEvents.length > 0 && (
        <TimelineView
          events={timelineEvents}
          title={`Forensic Event Timeline for ${account.account_id}`}
        />
      )}

      {/* Settled Transactions Table */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
        <h3 className="text-sm font-bold tracking-tight text-slate-200 flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          Settled Transaction Timeline ({transactions.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase font-semibold text-slate-400 bg-slate-800/40 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Transaction ID</th>
                <th className="py-2.5 px-3">Direction</th>
                <th className="py-2.5 px-3">Counterparty</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Scenario</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">
                    No transactions recorded for this account.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-mono text-cyan-400">{tx.transaction_id}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`font-semibold text-[10px] px-2 py-0.5 rounded ${
                          tx.direction === 'INCOMING'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-rose-500/10 text-rose-400'
                        }`}
                      >
                        {tx.direction}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <button
                        onClick={() => onSelectAccount(tx.counterparty)}
                        className="font-bold text-slate-200 hover:text-cyan-400 hover:underline"
                      >
                        {tx.counterparty}
                      </button>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-100">
                      ${tx.amount.toLocaleString()} {tx.currency}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {new Date(tx.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{tx.transaction_type}</td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">{tx.scenario_id || '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
