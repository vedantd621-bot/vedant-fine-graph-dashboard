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
  RefreshCw,
  Zap,
  Flame,
  Clock,
  Eye,
  CheckCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  CommandCenterSummary,
  Campaign,
  EnterpriseThreatAssessment,
  EnterpriseRiskForecast,
  EmergingNetwork,
  EarlyWarning,
  DiscoveredPattern,
} from '../types';

interface FraudCommandCenterPageProps {
  onNavigate: (tab: string) => void;
  onSelectCampaign?: (campaignId: string) => void;
  onSelectWarning?: (warningId: string) => void;
}

export const FraudCommandCenterPage: React.FC<FraudCommandCenterPageProps> = ({
  onNavigate,
  onSelectCampaign,
  onSelectWarning,
}) => {
  const [summary, setSummary] = useState<CommandCenterSummary | null>(null);
  const [threat, setThreat] = useState<EnterpriseThreatAssessment | null>(null);
  const [forecast, setForecast] = useState<EnterpriseRiskForecast | null>(null);
  const [emerging, setEmerging] = useState<EmergingNetwork[]>([]);
  const [warnings, setWarnings] = useState<EarlyWarning[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, advRes] = await Promise.all([
        apiClient.getCommandCenterSummary(),
        apiClient.getCommandCenterAdvancedSummary().catch(() => ({ data: null })),
      ]);
      setSummary(sumRes.data);
      if (advRes.data) {
        setThreat(advRes.data.threat);
        setForecast(advRes.data.forecast);
        setEmerging(advRes.data.emerging_networks || []);
        setWarnings(advRes.data.active_early_warnings || []);
      }
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
          <span>Loading Command Center V2...</span>
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
            <h1 className="text-xl font-bold text-slate-100">Enterprise Fraud Command Center V2</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time graph evolution, early warnings, time-series forecasting, and syndicate campaign tracking
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('early-warnings')}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium"
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Early Warnings ({warnings.length})</span>
          </button>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Enterprise Threat Level & Horizon Forecast */}
      {threat && forecast && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="p-4 bg-gradient-to-br from-slate-900 to-rose-950/40 border border-rose-500/30 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1">
                <Flame className="h-3.5 w-3.5" /> Enterprise Threat Level
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/40">
                {threat.threat_level}
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black text-slate-100">{threat.score}</span>
              <span className="text-xs text-slate-400">/ 100 Index</span>
            </div>
            <div className="text-[11px] text-slate-400 truncate">
              Drivers: {threat.drivers[0]}
            </div>
          </div>

          <div className="lg:col-span-2 p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> Time-Series Risk Forecast Curve
              </span>
              <span className="text-slate-400 text-[11px]">Confidence: {Math.round(forecast.confidence * 100)}%</span>
            </div>
            <div className="grid grid-cols-4 gap-2 pt-1">
              {[
                { label: 'Next 1h', val: forecast.forecast_1h },
                { label: 'Next 6h', val: forecast.forecast_6h },
                { label: 'Next 24h', val: forecast.forecast_24h },
                { label: 'Next 7d', val: forecast.forecast_7d },
              ].map((f) => (
                <div key={f.label} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-center space-y-0.5">
                  <div className="text-[10px] text-slate-400 font-medium">{f.label}</div>
                  <div className="text-lg font-bold text-amber-400">{f.val}</div>
                  <div className="text-[9px] text-slate-500">Projected Risk</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Investigations</span>
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{summary.active_investigations}</div>
          <div className="text-[11px] text-cyan-400/80 font-medium">{summary.open_fraud_cases} open cases</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Critical Alerts</span>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">{summary.critical_alerts}</div>
          <div className="text-[11px] text-rose-300/80 font-medium">Immediate triage required</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Confirmed Fraud Exposure</span>
            <DollarSign className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">${summary.confirmed_fraud_value.toLocaleString()}</div>
          <div className="text-[11px] text-slate-400">Potential: ${summary.potential_exposure.toLocaleString()}</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Campaigns</span>
            <Activity className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400">{summary.active_campaigns_count}</div>
          <div className="text-[11px] text-purple-300/80 font-medium">Syndicate clusters</div>
        </div>
      </div>

      {/* Emerging Networks & Active Early Warnings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emerging Networks */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <Activity className="h-4 w-4 text-cyan-400" /> Emerging Fraud Networks ({emerging.length})
            </span>
            <button onClick={() => onNavigate('network-evolution')} className="text-xs text-cyan-400 hover:underline">
              Evolution Center →
            </button>
          </div>
          <div className="divide-y divide-slate-800 text-xs">
            {emerging.map((emg) => (
              <div key={emg.network_id} className="py-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-100">{emg.name}</span>
                  <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold text-[10px]">
                    {emg.emergence_score} Score
                  </span>
                </div>
                <p className="text-slate-400 text-[11px]">{emg.explanation}</p>
              </div>
            ))}
            {emerging.length === 0 && (
              <div className="py-4 text-xs text-slate-500 italic">No newly emerging networks detected.</div>
            )}
          </div>
        </div>

        {/* Active Early Warnings */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4 text-rose-400" /> Active Early Warnings ({warnings.length})
            </span>
            <button onClick={() => onNavigate('early-warnings')} className="text-xs text-rose-400 hover:underline">
              Warning Center →
            </button>
          </div>
          <div className="divide-y divide-slate-800 text-xs">
            {warnings.map((w) => (
              <div key={w.warning_id} className="py-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100">{w.entity_type} {w.entity_id}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {w.severity}
                    </span>
                  </div>
                  <span className="text-amber-400 font-semibold">{w.recommended_action}</span>
                </div>
                <p className="text-slate-400 text-[11px]">{w.explanation}</p>
              </div>
            ))}
            {warnings.length === 0 && (
              <div className="py-4 text-xs text-slate-500 italic">Zero unacknowledged early warnings.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
