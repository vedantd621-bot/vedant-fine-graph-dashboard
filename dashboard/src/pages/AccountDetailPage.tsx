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
  TrendingUp,
  Zap,
  Compass,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  AccountDetail,
  AccountTransactionItem,
  EntityBehaviorResponse,
  EntityRiskProfile,
  EntitySimilarityResponse,
  GraphPayload,
  InvestigationTimelineEvent,
  TemporalWindow,
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
  const [behavior, setBehavior] = useState<EntityBehaviorResponse | null>(null);
  const [similarEntities, setSimilarEntities] = useState<EntitySimilarityResponse | null>(null);
  const [activeWindow, setActiveWindow] = useState<TemporalWindow>('24h');
  const [graphData, setGraphData] = useState<GraphPayload | null>(null);
  const [graphDepth, setGraphDepth] = useState<number>(2);
  const [suspiciousOnly, setSuspiciousOnly] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [freezing, setFreezing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountData = async () => {
    try {
      setLoading(true);
      const [accRes, txRes, gRes, profRes, tlRes, behRes, simRes] = await Promise.all([
        apiClient.getAccountDetail(accountId),
        apiClient.getAccountTransactions(accountId, { page: 1, page_size: 20 }),
        suspiciousOnly
          ? apiClient.getSuspiciousNeighborhood(accountId, 60.0)
          : apiClient.getAccountGraph(accountId, graphDepth),
        apiClient.getEntityRiskProfile(accountId).catch(() => null),
        apiClient.getEntityTimeline(accountId).catch(() => ({ events: [] })),
        apiClient.getEntityBehavior(accountId, activeWindow).catch(() => null),
        apiClient.getSimilarEntities(accountId, 4).catch(() => null),
      ]);
      setAccount(accRes);
      setTransactions(txRes.data);
      setGraphData(gRes);
      if (profRes) setRiskProfile(profRes);
      if (tlRes && tlRes.events) setTimelineEvents(tlRes.events);
      if (behRes) setBehavior(behRes);
      if (simRes) setSimilarEntities(simRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load account dossier.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccountData();
    realtimeClient.watchAccount(accountId);
  }, [accountId, graphDepth, suspiciousOnly, activeWindow]);

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
      setAccount((prev) => (prev ? { ...prev, is_frozen: res.is_frozen } : prev));
    } catch (err: any) {
      alert(err.response?.data?.detail?.message || 'Failed to toggle account freeze status.');
    } finally {
      setFreezing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center">
        <div className="h-8 w-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin mx-auto mb-3"></div>
        <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
          Loading Account Dossier...
        </span>
      </div>
    );
  }

  if (error || !account) {
    return (
      <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-4">
        <div className="text-rose-400 font-semibold">{error || 'Account not found.'}</div>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
        >
          Return to Accounts
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-cyan-400 transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Accounts List</span>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-100 font-mono">{account.account_id}</h1>
            {account.is_frozen && (
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-bold flex items-center gap-1.5">
                <Snowflake className="h-3.5 w-3.5" /> Frozen
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Account Type: <strong className="text-slate-200">{account.type}</strong> | Balance:{' '}
            <strong className="text-slate-200">${account.balance.toLocaleString()} {account.currency}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl">
            <span className="text-xs text-slate-400">Risk Score:</span>
            <span
              className={`text-base font-bold font-mono ${
                account.risk_level === 'CRITICAL'
                  ? 'text-rose-400'
                  : account.risk_level === 'HIGH'
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}
            >
              {account.risk_score.toFixed(1)} / 100 ({account.risk_level})
            </span>
          </div>

          {canFreeze && (
            <button
              onClick={handleToggleFreeze}
              disabled={freezing}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-md ${
                account.is_frozen
                  ? 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-extrabold shadow-cyan-950/40'
              }`}
            >
              <Snowflake className="h-4 w-4" />
              <span>{freezing ? 'Updating...' : account.is_frozen ? 'Unfreeze Account' : 'Freeze Account'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Owner Entity</span>
          <div className="text-sm font-semibold text-slate-200 flex items-center gap-1.5 mt-1">
            <Users className="h-4 w-4 text-cyan-400" />
            {account.owner_id ? `${account.owner_id} (${account.owner_type})` : 'Unassigned'}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Bank / Institution</span>
          <div className="text-sm font-semibold text-slate-200 flex items-center gap-1.5 mt-1">
            <Building className="h-4 w-4 text-cyan-400" />
            {account.bank_name || 'FinGraph Core'} ({account.bank_routing})
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">PageRank Centrality</span>
          <div className="text-sm font-mono font-bold text-slate-100 mt-1">
            {account.features.pagerank.toFixed(5)}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400">Community & Degree</span>
          <div className="text-sm font-semibold text-slate-200 mt-1">
            Cluster #{account.features.louvain_community_id ?? 'None'} • {account.features.total_degree} Links
          </div>
        </div>
      </div>

      {/* Behavioral Anomaly & Temporal Dossier */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-bold text-slate-100">Behavioral Baseline & Temporal Deviations</h3>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-400 mr-1">Window:</span>
            {(['5m', '1h', '24h', '7d', '30d'] as TemporalWindow[]).map((w) => (
              <button
                key={w}
                onClick={() => setActiveWindow(w)}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                  activeWindow === w
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {w}
              </button>
            ))}
          </div>
        </div>

        {behavior ? (
          <div className="space-y-4">
            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-300">
              <span className="font-semibold text-cyan-400">Diagnostic Summary: </span>
              {behavior.summary}
            </div>

            {/* Baseline vs Current stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-lg">
                <span className="text-slate-500 block">Avg Tx Amount</span>
                <span className="font-bold text-slate-200 font-mono mt-0.5 block">
                  ${behavior.baseline.avg_transaction_amount.toFixed(2)} (±${behavior.baseline.std_dev_amount.toFixed(2)})
                </span>
              </div>
              <div className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-lg">
                <span className="text-slate-500 block">Avg Velocity</span>
                <span className="font-bold text-slate-200 font-mono mt-0.5 block">
                  {behavior.baseline.avg_velocity_per_hour.toFixed(2)} tx/hr
                </span>
              </div>
              <div className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-lg">
                <span className="text-slate-500 block">Window Volume</span>
                <span className="font-bold text-slate-200 font-mono mt-0.5 block">
                  ${behavior.recent_volume.toFixed(2)} ({behavior.recent_transaction_count} tx)
                </span>
              </div>
              <div className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-lg">
                <span className="text-slate-500 block">Anomaly Score</span>
                <span className={`font-bold font-mono mt-0.5 block ${behavior.anomaly_score >= 60 ? 'text-rose-400' : 'text-slate-300'}`}>
                  {behavior.anomaly_score.toFixed(1)} / 100
                </span>
              </div>
            </div>

            {/* Detected Anomalies List */}
            {behavior.anomalies.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                  Active Behavioral Deviations ({behavior.anomalies.length})
                </span>
                <div className="space-y-2">
                  {behavior.anomalies.map((anom) => (
                    <div
                      key={anom.anomaly_id}
                      className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg flex items-start justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-rose-300">{anom.anomaly_type}</span>
                          <span className="px-1.5 py-0.5 bg-rose-500/20 text-rose-400 text-[10px] font-bold rounded">
                            {anom.deviation_ratio.toFixed(1)}x baseline
                          </span>
                        </div>
                        <p className="text-slate-400">{anom.description}</p>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono shrink-0">
                        {new Date(anom.detected_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-slate-500 text-center py-4">Calculating behavioral baseline...</div>
        )}
      </div>

      {/* Similar Suspect Entities */}
      {similarEntities && similarEntities.similar_entities.length > 0 && (
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md space-y-3">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Compass className="h-4 w-4 text-cyan-400" />
            Topological & Behavioral Peer Similarity
          </h3>
          <p className="text-xs text-slate-400">
            Entities sharing high counterparty overlap, community co-membership, and transaction profiles.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {similarEntities.similar_entities.map((sim) => (
              <div
                key={sim.target_entity_id}
                onClick={() => onSelectAccount(sim.target_entity_id)}
                className="p-3.5 bg-slate-950/60 hover:bg-slate-950 border border-slate-800 hover:border-cyan-500/30 rounded-xl transition-all cursor-pointer space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-cyan-400">{sim.target_entity_id}</span>
                  <span className="px-2 py-0.5 bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold rounded text-[11px]">
                    {(sim.similarity_score * 100).toFixed(0)}% Similarity
                  </span>
                </div>
                <p className="text-slate-400 text-[11px]">{sim.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

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
