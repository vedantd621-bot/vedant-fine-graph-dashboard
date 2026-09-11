import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  ShieldAlert,
  DollarSign,
  Activity,
  AlertTriangle,
  Lightbulb,
  Layers,
  RefreshCw,
  BarChart2
} from 'lucide-react';
import { EnterpriseKPIBundle, FraudTrendPoint } from '../types/enterprise';

export const AnalyticsExplorerPage: React.FC = () => {
  const [bundle, setBundle] = useState<EnterpriseKPIBundle | null>(null);
  const [trends, setTrends] = useState<FraudTrendPoint[]>([]);
  const [activeWindow, setActiveWindow] = useState<'DAILY' | 'WEEKLY' | 'HOURLY'>('DAILY');
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const apiBase = (process.env.REACT_APP_API_BASE_URL) || 'http://localhost:8000';
      const token = localStorage.getItem('fingraph_token') || localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const [kpiRes, trendRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/analytics/kpis`, { headers }),
        fetch(`${apiBase}/api/v1/analytics/trends?window=${activeWindow}&periods=14`, { headers }),
      ]);

      if (kpiRes.ok) {
        const kpiData = await kpiRes.json();
        setBundle(kpiData);
      }
      if (trendRes.ok) {
        const trendData = await trendRes.json();
        setTrends(trendData);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [activeWindow]);

  if (loading && !bundle) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading Enterprise Analytics Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex justify-between items-center bg-gray-900/60 p-6 rounded-xl border border-gray-800 backdrop-blur">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BarChart2 className="w-7 h-7 text-blue-400" />
            Enterprise Analytics Explorer
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Real-time fraud KPIs, multi-dimensional exposure metrics, and anomaly detection.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-800 p-1 rounded-lg border border-gray-700">
            {(['HOURLY', 'DAILY', 'WEEKLY'] as const).map((w) => (
              <button
                key={w}
                onClick={() => setActiveWindow(w)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                  activeWindow === w
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {w}
              </button>
            ))}
          </div>
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm border border-gray-700 transition"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {bundle && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Fraud Rate</p>
                <h3 className="text-2xl font-bold text-red-400 mt-1">
                  {(bundle.fraud.fraud_rate * 100).toFixed(1)}%
                </h3>
                <p className="text-xs text-gray-500 mt-1">{bundle.fraud.confirmed_fraud} Confirmed / {bundle.fraud.fraud_count} Flagged</p>
              </div>
              <div className="p-2.5 bg-red-500/10 rounded-lg border border-red-500/20">
                <ShieldAlert className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Prevented Loss</p>
                <h3 className="text-2xl font-bold text-green-400 mt-1">
                  ${(bundle.financial.prevented_loss / 1000).toFixed(0)}k
                </h3>
                <p className="text-xs text-gray-500 mt-1">${(bundle.financial.confirmed_fraud_exposure / 1000).toFixed(0)}k at risk</p>
              </div>
              <div className="p-2.5 bg-green-500/10 rounded-lg border border-green-500/20">
                <DollarSign className="w-5 h-5 text-green-400" />
              </div>
            </div>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">SLA Compliance</p>
                <h3 className="text-2xl font-bold text-blue-400 mt-1">
                  {(bundle.operations.sla_compliance_rate * 100).toFixed(1)}%
                </h3>
                <p className="text-xs text-gray-500 mt-1">{bundle.operations.queue_depth} Queue Depth • {bundle.operations.investigation_backlog} Backlog</p>
              </div>
              <div className="p-2.5 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <Activity className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </div>

          <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Executive Posture</p>
                <h3 className="text-2xl font-bold text-amber-400 mt-1">
                  {bundle.posture.posture_score} / 100
                </h3>
                <p className="text-xs text-gray-500 mt-1">Threat Level: {bundle.posture.threat_level}</p>
              </div>
              <div className="p-2.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <Layers className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trend Table / Graph Preview */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-400" />
          Fraud Trend Trajectory ({activeWindow})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 font-medium text-xs">
                <th className="pb-3 px-3">TIMESTAMP</th>
                <th className="pb-3 px-3">FRAUD COUNT</th>
                <th className="pb-3 px-3">ALERT VOLUME</th>
                <th className="pb-3 px-3">AVG RISK SCORE</th>
                <th className="pb-3 px-3">FINANCIAL EXPOSURE</th>
                <th className="pb-3 px-3">DATA CONFIDENCE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {trends.slice(0, 7).map((t, idx) => (
                <tr key={idx} className="hover:bg-gray-800/30 transition">
                  <td className="py-3 px-3 text-gray-300 font-mono text-xs">{new Date(t.timestamp).toLocaleDateString()}</td>
                  <td className="py-3 px-3 text-red-400 font-semibold">{t.fraud_count}</td>
                  <td className="py-3 px-3 text-gray-300">{t.alert_volume}</td>
                  <td className="py-3 px-3 text-amber-300">{t.risk_average}</td>
                  <td className="py-3 px-3 text-green-400 font-mono">${t.exposure.toLocaleString()}</td>
                  <td className="py-3 px-3 text-gray-400">{(t.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights & Anomalies Grid */}
      {bundle && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Executive Insights */}
          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              Evidence-Backed Executive Insights
            </h3>
            <div className="space-y-3">
              {bundle.insights.map((ins) => (
                <div key={ins.insight_id} className="p-4 bg-gray-800/40 border border-gray-800 rounded-lg">
                  <div className="flex justify-between items-start">
                    <h4 className="text-sm font-semibold text-white">{ins.title}</h4>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">
                      {ins.severity}
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 mt-1">{ins.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {ins.evidence.map((ev, eIdx) => (
                      <span key={eIdx} className="text-[10px] bg-gray-700/60 text-gray-300 px-2 py-0.5 rounded">
                        ✓ {ev}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* KPI Anomalies */}
          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Statistical KPI Anomalies
            </h3>
            <div className="space-y-3">
              {bundle.anomalies.map((anom) => (
                <div key={anom.anomaly_id} className="p-4 bg-red-950/20 border border-red-900/40 rounded-lg">
                  <div className="flex justify-between items-start">
                    <h4 className="text-sm font-semibold text-red-200 font-mono">{anom.metric}</h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-300">
                      +{anom.deviation.toFixed(1)}% DEVIATION
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 mt-1">{anom.explanation}</p>
                  <div className="text-[11px] text-gray-400 mt-2 font-mono">
                    Baseline: {anom.baseline} → Current: {anom.current}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AnalyticsExplorerPage;
