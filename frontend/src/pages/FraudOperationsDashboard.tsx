import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Users,
  Activity,
  DollarSign,
  BarChart3,
  Layers,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { apiService } from '../api/client';
import {
  OperationsSummary,
  FraudTrendsResponse,
  DetectorPerformanceResponse,
  SLASummary,
} from '../types';

interface FraudOperationsDashboardProps {
  onNavigate?: (tab: string) => void;
}

export const FraudOperationsDashboard: React.FC<FraudOperationsDashboardProps> = ({ onNavigate }) => {
  const [summary, setSummary] = useState<OperationsSummary | null>(null);
  const [trends, setTrends] = useState<FraudTrendsResponse | null>(null);
  const [detectors, setDetectors] = useState<DetectorPerformanceResponse | null>(null);
  const [sla, setSla] = useState<SLASummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [trendInterval, setTrendInterval] = useState<'hourly' | 'daily'>('hourly');

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumRes, trendsRes, detRes, slaRes] = await Promise.all([
        apiService.getOperationsSummary(),
        apiService.getFraudTrends(trendInterval, 7),
        apiService.getDetectorPerformance(),
        apiService.getSLASummary(),
      ]);
      if (sumRes) setSummary(sumRes);
      if (trendsRes) setTrends(trendsRes);
      if (detRes) setDetectors(detRes);
      if (slaRes) setSla(slaRes);
    } catch (err) {
      console.error('Failed to load executive fraud operations dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [trendInterval]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Executive Fraud Operations Dashboard</h1>
          <p className="text-sm text-slate-400">
            Real-time operational KPIs, time-series fraud trends, detector confirmation rates, and SLA compliance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Metrics</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Alerts Processed Today</span>
          <div className="text-2xl font-bold text-cyan-400">{summary?.alerts_today || 0}</div>
          <span className="text-[11px] text-slate-500">Across all detection rules</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Critical P0/P1 Alerts</span>
          <div className="text-2xl font-bold text-rose-400">{summary?.critical_alerts || 0}</div>
          <span className="text-[11px] text-rose-500/80">High urgency priority</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Confirmed Fraud Value</span>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            ${(summary?.total_fraud_value_prevented || 0).toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-500">Investigator validated / blocked</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">SLA Compliance Rate</span>
          <div className="text-2xl font-bold text-cyan-400">
            {summary ? `${summary.sla_compliance_rate.toFixed(1)}%` : '100%'}
          </div>
          <span className="text-[11px] text-slate-500">Target: &ge; 95%</span>
        </div>
      </div>

      {/* Dual Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time-Series Trend Charts */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-cyan-400" />
              Time-Series Fraud Volume & Value Trends
            </h2>
            <div className="flex items-center gap-1 bg-slate-800 p-0.5 rounded-lg text-xs">
              <button
                onClick={() => setTrendInterval('hourly')}
                className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
                  trendInterval === 'hourly' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Hourly (24h)
              </button>
              <button
                onClick={() => setTrendInterval('daily')}
                className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
                  trendInterval === 'daily' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Daily (7d)
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {trends && trends.points.map((p, idx) => (
              <div key={idx} className="space-y-1 text-xs">
                <div className="flex items-center justify-between text-slate-400">
                  <span>{new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  <div className="space-x-3">
                    <span className="text-slate-300 font-semibold">{p.alert_count} alerts</span>
                    <span className="text-rose-400 font-semibold">{p.critical_count} critical</span>
                    <span className="text-emerald-400 font-mono">${p.fraud_amount.toLocaleString()}</span>
                  </div>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex">
                  <div
                    className="bg-cyan-500 h-2"
                    style={{ width: `${Math.min(100, (p.alert_count / (trends.total_alerts || 1)) * 100)}%` }}
                  ></div>
                  <div
                    className="bg-rose-500 h-2"
                    style={{ width: `${Math.min(100, (p.critical_count / (trends.total_alerts || 1)) * 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SLA Compliance Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-400" />
              SLA Health Breakdown
            </h2>
          </div>

          <div className="space-y-4">
            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Within SLA</span>
                <span className="text-emerald-400 font-bold">{sla?.within_sla_count || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">At Risk (&lt;25% SLA left)</span>
                <span className="text-amber-400 font-bold">{sla?.at_risk_count || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Breached SLA</span>
                <span className="text-rose-400 font-bold">{sla?.breached_count || 0}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-1">
              <span className="text-xs font-semibold text-slate-300">Active Fraud Networks</span>
              <div className="text-xl font-bold text-cyan-400">{summary?.active_networks_count || 0}</div>
              <p className="text-[11px] text-slate-500">Discovered collusive rings and funnel clusters</p>
            </div>
          </div>
        </div>
      </div>

      {/* Detector Performance Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Detector Operational Confirmation Analytics
            </h2>
            <p className="text-xs text-slate-500">
              Measures investigator confirmation rate across Cypher graph pattern rules (distinct from ML precision/recall).
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="p-3">Detector Rule</th>
                <th className="p-3">Alerts Generated</th>
                <th className="p-3">Confirmed Fraud</th>
                <th className="p-3">False Positives</th>
                <th className="p-3">Confirmation Rate</th>
                <th className="p-3">Avg Risk Score</th>
                <th className="p-3 text-right">Total Exposure</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {detectors && detectors.detectors.map((d) => (
                <tr key={d.detection_type} className="hover:bg-slate-800/40">
                  <td className="p-3 font-semibold text-slate-200">{d.detection_type}</td>
                  <td className="p-3 font-mono">{d.alert_count}</td>
                  <td className="p-3 font-mono text-emerald-400">{d.confirmed_fraud_count}</td>
                  <td className="p-3 font-mono text-slate-500">{d.false_positive_count}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
                      {d.operational_confirmation_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="p-3 font-mono">{d.avg_risk_score.toFixed(1)}/100</td>
                  <td className="p-3 text-right font-mono text-slate-200">${d.total_amount.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
