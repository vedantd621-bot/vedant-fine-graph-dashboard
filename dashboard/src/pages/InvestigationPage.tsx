import React, { useState } from 'react';
import {
  Search,
  Compass,
  ArrowRight,
  ShieldAlert,
  Users,
  DollarSign,
  Layers,
  ArrowDownRight,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { MoneyTrailPath, SearchResults } from '../types';

interface InvestigationPageProps {
  onSelectAccount: (accountId: string) => void;
  onSelectAlert: (alertId: string) => void;
  initialQuery?: string;
}

export const InvestigationPage: React.FC<InvestigationPageProps> = ({
  onSelectAccount,
  onSelectAlert,
  initialQuery = '',
}) => {
  const [activeTab, setActiveTab] = useState<'trail' | 'search'>('trail');

  // Money Trail state
  const [fromAccount, setFromAccount] = useState<string>('A001');
  const [toAccount, setToAccount] = useState<string>('A006');
  const [maxHops, setMaxHops] = useState<number>(4);
  const [trailPaths, setTrailPaths] = useState<MoneyTrailPath[]>([]);
  const [trailLoading, setTrailLoading] = useState<boolean>(false);
  const [trailError, setTrailError] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>(initialQuery);
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);

  const handleTraceMoneyTrail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromAccount.trim()) return;

    try {
      setTrailLoading(true);
      setTrailError(null);
      const paths = await apiClient.traceMoneyTrail(
        fromAccount.trim(),
        toAccount.trim() || undefined,
        maxHops
      );
      setTrailPaths(paths);
    } catch (err: any) {
      setTrailError(err.message || 'Failed to trace money trail.');
    } finally {
      setTrailLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearchLoading(true);
      const results = await apiClient.searchEntities(searchQuery.trim());
      setSearchResults(results);
    } catch (err: any) {
      console.error('Search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">Forensic Investigation Tools</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Trace multi-hop fund flow trails across banking institutions and search transaction entities.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('trail')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'trail'
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Compass className="h-4 w-4" /> Multi-Hop Money Trail Tracer
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'search'
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Search className="h-4 w-4" /> Universal Entity Search
        </button>
      </div>

      {/* Tab 1: Money Trail Tracer */}
      {activeTab === 'trail' && (
        <div className="space-y-6">
          <form
            onSubmit={handleTraceMoneyTrail}
            className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-4"
          >
            <h3 className="text-sm font-bold text-slate-200">Trace Directed Fund Flow</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">
                  Origin Account (From)
                </label>
                <input
                  type="text"
                  placeholder="e.g. A001"
                  value={fromAccount}
                  onChange={(e) => setFromAccount(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">
                  Destination Account (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. A006"
                  value={toAccount}
                  onChange={(e) => setToAccount(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Max Hops Depth</label>
                <select
                  value={maxHops}
                  onChange={(e) => setMaxHops(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value={2}>2 Hops</option>
                  <option value={3}>3 Hops</option>
                  <option value={4}>4 Hops (Recommended)</option>
                  <option value={5}>5 Hops</option>
                  <option value={6}>6 Hops</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={trailLoading}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition-colors flex items-center gap-2"
            >
              <Compass className="h-4 w-4" />
              {trailLoading ? 'Tracing Graph Paths...' : 'Discover Money Trail'}
            </button>
          </form>

          {/* Results Display */}
          {trailError && (
            <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {trailError}
            </div>
          )}

          {trailPaths.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-200">
                Discovered Directed Trails ({trailPaths.length})
              </h3>
              <div className="space-y-3">
                {trailPaths.map((path, idx) => (
                  <div
                    key={path.path_id || idx}
                    className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-cyan-400">Path #{idx + 1}</span>
                        <span className="text-xs text-slate-400 font-medium">
                          ({path.hop_count} hops · Total Volume: ${path.total_amount.toLocaleString()} USD)
                        </span>
                      </div>
                    </div>

                    {/* Path Nodes Visual Flow */}
                    <div className="flex flex-wrap items-center gap-2 py-2">
                      {path.path_nodes.map((nodeId, nodeIdx) => (
                        <React.Fragment key={nodeId}>
                          <button
                            onClick={() => onSelectAccount(nodeId)}
                            className={`px-3 py-1.5 rounded-lg font-mono font-bold text-xs transition-colors ${
                              nodeIdx === 0
                                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                                : nodeIdx === path.path_nodes.length - 1
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-slate-800 text-slate-200 border border-slate-700 hover:border-cyan-500'
                            }`}
                          >
                            {nodeId}
                          </button>
                          {nodeIdx < path.path_nodes.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-slate-500 shrink-0" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>

                    {/* Step Breakdown */}
                    <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                      {path.steps.map((st, sIdx) => (
                        <div
                          key={sIdx}
                          className="flex items-center justify-between text-xs text-slate-300 py-1"
                        >
                          <div className="flex items-center gap-2">
                            <ArrowDownRight className="h-3.5 w-3.5 text-cyan-400" />
                            <span className="font-mono text-cyan-300">{st.from_account}</span>
                            <span className="text-slate-500">→</span>
                            <span className="font-mono text-cyan-300">{st.to_account}</span>
                            <span className="text-slate-400 font-mono text-[11px]">({st.transaction_id})</span>
                          </div>
                          <span className="font-semibold text-slate-100">
                            ${st.amount.toLocaleString()} {st.currency}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Universal Search */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Enter Account ID, Transaction ID, or Alert ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={searchLoading}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition-colors flex items-center gap-2"
            >
              <Search className="h-4 w-4" />
              Search
            </button>
          </form>

          {searchResults && (
            <div className="space-y-6">
              {/* Accounts */}
              {searchResults.accounts.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-200">
                    Matched Accounts ({searchResults.accounts.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {searchResults.accounts.map((acc) => (
                      <div
                        key={acc.account_id}
                        onClick={() => onSelectAccount(acc.account_id)}
                        className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-cyan-400">{acc.account_id}</span>
                          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            {acc.risk_level} RISK ({acc.risk_score.toFixed(1)})
                          </span>
                        </div>
                        <div className="text-xs text-slate-400">Owner: {acc.owner_name || '—'} · Bank: {acc.bank_name || '—'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Alerts */}
              {searchResults.alerts.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-200">
                    Matched Alerts ({searchResults.alerts.length})
                  </h3>
                  <div className="space-y-2">
                    {searchResults.alerts.map((alt) => (
                      <div
                        key={alt.alert_id}
                        onClick={() => onSelectAlert(alt.alert_id)}
                        className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500 cursor-pointer transition-colors flex items-center justify-between"
                      >
                        <div>
                          <div className="font-mono font-bold text-cyan-400 text-xs">{alt.alert_id} ({alt.detection_type})</div>
                          <div className="text-xs text-slate-300">{alt.description}</div>
                        </div>
                        <span className="text-xs font-bold text-slate-400">{alt.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
