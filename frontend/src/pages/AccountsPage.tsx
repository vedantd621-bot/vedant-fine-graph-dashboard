import React, { useEffect, useState } from 'react';
import { Users, Search, ArrowRight, Snowflake, ShieldAlert } from 'lucide-react';
import { apiClient } from '../api/client';
import { AccountSummary, RiskLevel } from '../types';

interface AccountsPageProps {
  onSelectAccount: (accountId: string) => void;
}

export const AccountsPage: React.FC<AccountsPageProps> = ({ onSelectAccount }) => {
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('risk_score');
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.listAccounts({
        risk_level: riskFilter || undefined,
        search: searchQuery || undefined,
        sort: sortBy,
        order: 'desc',
        page,
        page_size: 15,
      });
      setAccounts(res.data);
      setTotalPages(res.pagination.total_pages);
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [riskFilter, sortBy, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchAccounts();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">Account Dossiers</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Network centrality, GDS community clustering, and composite risk evaluations.
          </p>
        </div>
      </div>

      {/* Filters & Search Form */}
      <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Account ID (e.g. A005)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Risk Level Filter */}
        <select
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Risk Levels</option>
          <option value="CRITICAL">Critical (75-100)</option>
          <option value="HIGH">High (50-74)</option>
          <option value="MEDIUM">Medium (25-49)</option>
          <option value="LOW">Low (0-24)</option>
        </select>

        {/* Sort Field */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="risk_score">Sort by Risk Score</option>
          <option value="total_volume">Sort by Volume</option>
          <option value="pagerank">Sort by PageRank</option>
          <option value="account_id">Sort by Account ID</option>
        </select>
      </form>

      {/* Accounts Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase font-semibold text-slate-400 bg-slate-800/40 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Account</th>
                <th className="py-3 px-4">Owner / Entity</th>
                <th className="py-3 px-4">Host Bank</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">PageRank</th>
                <th className="py-3 px-4">Degree</th>
                <th className="py-3 px-4">Community</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading accounts...
                  </td>
                </tr>
              ) : accounts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No accounts found matching criteria.
                  </td>
                </tr>
              ) : (
                accounts.map((acc) => {
                  const isCrit = acc.risk_level === 'CRITICAL';
                  const isHigh = acc.risk_level === 'HIGH';
                  return (
                    <tr
                      key={acc.account_id}
                      onClick={() => onSelectAccount(acc.account_id)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-slate-100">{acc.account_id}</td>
                      <td className="py-3 px-4 text-slate-300">{acc.owner_name || acc.owner_id || '—'}</td>
                      <td className="py-3 px-4 text-slate-400">{acc.bank_name || acc.bank_id || '—'}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-bold px-2 py-0.5 rounded text-[10px] uppercase border ${
                            isCrit
                              ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                              : isHigh
                              ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                              : 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                          }`}
                        >
                          {acc.risk_score.toFixed(1)} ({acc.risk_level})
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{acc.pagerank.toFixed(3)}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {acc.total_degree} (In {acc.in_degree} · Out {acc.out_degree})
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {acc.louvain_community_id !== undefined ? `Group ${acc.louvain_community_id}` : '—'}
                      </td>
                      <td className="py-3 px-4">
                        {acc.is_frozen ? (
                          <span className="flex items-center gap-1 text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                            <Snowflake className="h-3 w-3" /> FROZEN
                          </span>
                        ) : (
                          <span className="text-[11px] text-emerald-400">ACTIVE</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAccount(acc.account_id);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 font-semibold transition-colors"
                        >
                          Dossier
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
