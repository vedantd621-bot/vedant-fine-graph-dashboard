import React, { useEffect, useState } from 'react';
import {
  Share2,
  AlertTriangle,
  Users,
  Layers,
  ArrowRight,
  RefreshCw,
  Search,
  Filter,
  ShieldCheck,
  ShieldAlert,
  SlidersHorizontal,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { NetworkListResponse, NetworkSummary, NetworkType, RiskLevel } from '../types';
import { useAuth } from '../auth/AuthContext';

interface FraudNetworksPageProps {
  onSelectNetwork: (networkId: string) => void;
  onSelectAccount: (accountId: string) => void;
}

export const FraudNetworksPage: React.FC<FraudNetworksPageProps> = ({
  onSelectNetwork,
  onSelectAccount,
}) => {
  const { hasRole } = useAuth();
  const [networks, setNetworks] = useState<NetworkSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [discovering, setDiscovering] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<string>('ALL');
  const [minRiskScore, setMinRiskScore] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);

  const fetchNetworks = async () => {
    try {
      setLoading(true);
      const params: any = { page, page_size: 12 };
      if (selectedType !== 'ALL') params.network_type = selectedType;
      if (selectedRiskLevel !== 'ALL') params.risk_level = selectedRiskLevel;
      if (minRiskScore > 0) params.min_risk_score = minRiskScore;
      if (searchTerm.trim()) params.search = searchTerm.trim();

      const res: NetworkListResponse = await apiClient.listNetworks(params);
      setNetworks(res.data);
      setTotalPages(res.pagination.total_pages);
      setTotalItems(res.pagination.total_items);
    } catch (err) {
      console.error('Failed to fetch fraud networks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetworks();
  }, [page, selectedType, selectedRiskLevel, minRiskScore]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchNetworks();
  };

  const handleDiscover = async () => {
    try {
      setDiscovering(true);
      await apiClient.discoverNetworks(true);
      await fetchNetworks();
    } catch (err) {
      console.error('Network discovery failed:', err);
    } finally {
      setDiscovering(false);
    }
  };

  const getRiskBadge = (level: RiskLevel) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'MEDIUM':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
  };

  const getTypeLabel = (type: NetworkType) => {
    switch (type) {
      case 'CIRCULAR_RING':
        return 'Circular Flow Ring';
      case 'FAN_IN_CONSOLIDATION':
        return 'Fan-In Consolidation';
      case 'FAN_OUT_DISPERSION':
        return 'Fan-Out Dispersion';
      case 'LAYERED_CHAIN':
        return 'Layered Chain';
      case 'COMMUNITY_SYNDICATE':
        return 'Community Syndicate';
      case 'SHARED_INFRASTRUCTURE':
        return 'Shared Counterparty Hub';
      default:
        return type;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
            <Share2 className="h-4 w-4" />
            <span>Fraud Syndicate & Network Intelligence</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mt-1">Collusive Fraud Networks</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Automated discovery of laundering rings, layered chains, consolidation funnels, and Louvain syndicates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDiscover}
            disabled={discovering}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-cyan-900/30 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${discovering ? 'animate-spin' : ''}`} />
            <span>{discovering ? 'Discovering Rings...' : 'Run Network Discovery'}</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[260px] relative">
          <Search className="h-4 w-4 absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by network ID, name, or account ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </form>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Filter className="h-3.5 w-3.5" />
            <span>Type:</span>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-800 text-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:border-cyan-500/50"
            >
              <option value="ALL">All Types</option>
              <option value="CIRCULAR_RING">Circular Ring</option>
              <option value="FAN_IN_CONSOLIDATION">Fan-In Funnel</option>
              <option value="FAN_OUT_DISPERSION">Fan-Out Dispersion</option>
              <option value="LAYERED_CHAIN">Layered Chain</option>
              <option value="COMMUNITY_SYNDICATE">Community Syndicate</option>
              <option value="SHARED_INFRASTRUCTURE">Shared Hub</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Risk:</span>
            <select
              value={selectedRiskLevel}
              onChange={(e) => {
                setSelectedRiskLevel(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-800 text-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:border-cyan-500/50"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grid of Network Cards */}
      {loading ? (
        <div className="p-12 text-center">
          <div className="h-8 w-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin mx-auto mb-3"></div>
          <span className="text-xs text-slate-400">Analyzing network topologies...</span>
        </div>
      ) : networks.length === 0 ? (
        <div className="p-12 bg-slate-900/40 border border-slate-800/80 rounded-2xl text-center space-y-3">
          <ShieldCheck className="h-12 w-12 text-slate-500 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No Fraud Networks Discovered</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            No collusive rings or syndicates matching the filter criteria were found. Click "Run Network Discovery" to scan the transaction graph.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {networks.map((net) => (
            <div
              key={net.network_id}
              onClick={() => onSelectNetwork(net.network_id)}
              className="group p-5 bg-slate-900/70 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-xl transition-all cursor-pointer shadow-lg hover:shadow-cyan-950/20 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                      {net.network_id}
                    </span>
                    <h3 className="text-base font-bold text-slate-100 group-hover:text-cyan-400 transition-colors line-clamp-1">
                      {net.name}
                    </h3>
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${getRiskBadge(
                      net.risk_level
                    )}`}
                  >
                    {net.risk_level} {net.risk_score.toFixed(0)}
                  </span>
                </div>

                <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                  <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-slate-300">
                    {getTypeLabel(net.network_type)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px] block">Members</span>
                    <span className="font-semibold text-slate-200 flex items-center gap-1 mt-0.5">
                      <Users className="h-3.5 w-3.5 text-slate-400" />
                      {net.total_members} Accounts
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Aggregated Volume</span>
                    <span className="font-semibold text-slate-200 mt-0.5 block font-mono">
                      ${net.total_volume.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {net.hub_account_id && (
                  <div className="text-[11px] text-slate-400 bg-slate-950/50 p-2 rounded border border-slate-800/50">
                    <span className="text-slate-500">Hub: </span>
                    <span className="font-mono text-slate-300">{net.hub_account_id}</span>
                  </div>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-cyan-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                <span>Investigate Network</span>
                <ArrowRight className="h-4 w-4" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs text-slate-400">
          <span>
            Showing page {page} of {totalPages} ({totalItems} networks total)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded hover:bg-slate-800 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded hover:bg-slate-800 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
