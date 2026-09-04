import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Users,
  Activity,
  DollarSign,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { CommandCenterSummary, Campaign, EnterpriseFraudPosture } from '../types';

interface FraudCommandCenterPageProps {
  onNavigate: (tab: string) => void;
  onSelectCampaign?: (campaignId: string) => void;
}

export const FraudCommandCenterPage: React.FC<FraudCommandCenterPageProps> = ({
  onNavigate,
  onSelectCampaign,
}) => {
  const [summary, setSummary] = useState<CommandCenterSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getCommandCenterSummary();
      setSummary(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load command center data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5 animate-spin text-cyan-400" />
          <span>Loading Enterprise Command Center...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl">
        Failed to load enterprise command center: {error}
      </div>
    );
  }

  const { posture } = summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Zap className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">Enterprise Fraud Command Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time cross-case intelligence, active syndicate campaigns, and enterprise defense posture
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Investigations</span>
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{summary.active_investigations}</div>
          <div className="text-[11px] text-cyan-400/80 font-medium">
            {summary.open_fraud_cases} open cases
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Critical Alerts</span>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">{summary.critical_alerts}</div>
          <div className="text-[11px] text-rose-300/80 font-medium">Requiring immediate triage</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Confirmed Fraud Exposure</span>
            <DollarSign className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            ${summary.confirmed_fraud_value.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400">
            Potential: ${summary.potential_exposure.toLocaleString()}
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Campaigns</span>
            <Activity className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400">{summary.active_campaigns_count}</div>
          <div className="text-[11px] text-purple-300/80 font-medium">Syndicate operations</div>
        </div>
      </div>

      {/* Posture Score & Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 border border-cyan-500/20 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
              Enterprise Defense Posture
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30">
              {posture.risk_level}
            </span>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-black text-slate-100">{posture.posture_score}</span>
            <span className="text-sm font-semibold text-slate-400">/ 100</span>
            <span className={`text-xs font-semibold ${posture.score_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {posture.score_delta >= 0 ? `+${posture.score_delta}` : posture.score_delta} pts
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">{posture.summary}</p>

          <div className="pt-2 border-t border-slate-800 space-y-2 text-xs">
            <div className="font-semibold text-slate-300">Driver Attribution:</div>
            {posture.top_drivers.map((d, i) => (
              <div key={i} className="flex items-start justify-between gap-2">
                <span className="text-slate-400">{d.factor_name}</span>
                <span
                  className={`font-semibold shrink-0 ${
                    d.impact === 'POSITIVE' ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {d.score_contribution > 0 ? `+${d.score_contribution}` : d.score_contribution} pts
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Active Campaigns */}
        <div className="lg:col-span-2 p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-purple-400" />
              <span className="text-sm font-bold text-slate-200">Active Fraud Campaigns & Syndicates</span>
            </div>
            <button
              onClick={() => onNavigate('cases')}
              className="flex items-center gap-1 text-xs text-cyan-400 hover:underline"
            >
              <span>View Cases</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-800">
            {summary.top_campaigns.map((c) => (
              <div
                key={c.campaign_id}
                onClick={() => onSelectCampaign && onSelectCampaign(c.campaign_id)}
                className="py-3 flex items-center justify-between hover:bg-slate-800/40 px-2 rounded-lg cursor-pointer transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-slate-100">{c.name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      {c.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 max-w-lg truncate">{c.description}</p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500">
                    <span>{c.case_ids.length} Cases</span>
                    <span>•</span>
                    <span>{c.account_ids.length} Accounts</span>
                    <span>•</span>
                    <span>Exposure: ${c.financial_exposure.toLocaleString()}</span>
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <div className="text-xs font-bold text-rose-400">{c.risk_score} Risk</div>
                  <div className="text-[10px] text-slate-400">{Math.round(c.confidence * 100)}% Conf</div>
                </div>
              </div>
            ))}
            {summary.top_campaigns.length === 0 && (
              <div className="py-6 text-center text-xs text-slate-500">No active campaigns discovered.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
