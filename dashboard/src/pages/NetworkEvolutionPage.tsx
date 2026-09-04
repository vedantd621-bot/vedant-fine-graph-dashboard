import React, { useState, useEffect } from 'react';
import {
  Activity,
  TrendingUp,
  RefreshCw,
  Clock,
  Zap,
  ArrowRight,
  ShieldAlert,
  BarChart2,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  EvolutionTimeWindow,
  NetworkEvolutionSnapshot,
  NetworkRiskForecast,
} from '../types';

export const NetworkEvolutionPage: React.FC = () => {
  const [networkId, setNetworkId] = useState('NET-001');
  const [window, setWindow] = useState<EvolutionTimeWindow>('1h');
  const [snapshot, setSnapshot] = useState<NetworkEvolutionSnapshot | null>(null);
  const [forecast, setForecast] = useState<NetworkRiskForecast | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [evoRes, foreRes] = await Promise.all([
        apiClient.getNetworkEvolution(networkId, window),
        apiClient.getNetworkForecast(networkId),
      ]);
      setSnapshot(evoRes.data);
      setForecast(foreRes.data);
    } catch (err) {
      console.error('Failed to load network evolution:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [networkId, window]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Activity className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">Network Evolution & Trajectory Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Bounded snapshot differential tracking, velocity metrics, and time-series risk forecasting
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <select
            value={window}
            onChange={(e) => setWindow(e.target.value as EvolutionTimeWindow)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200"
          >
            <option value="5m">Window: 5 Minutes</option>
            <option value="1h">Window: 1 Hour</option>
            <option value="6h">Window: 6 Hours</option>
            <option value="24h">Window: 24 Hours</option>
            <option value="7d">Window: 7 Days</option>
            <option value="30d">Window: 30 Days</option>
          </select>
          <button
            onClick={loadData}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading network evolution snapshot...</div>
      ) : snapshot ? (
        <div className="space-y-6">
          {/* Overview Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
              <div className="text-xs text-slate-400">Growth Rate</div>
              <div className="text-2xl font-bold text-cyan-400">+{snapshot.growth_rate}%</div>
              <div className="text-[11px] text-slate-500">Nodes: {snapshot.current_snapshot.node_count}</div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
              <div className="text-xs text-slate-400">Risk Trajectory</div>
              <div className="text-xl font-bold text-amber-400">{snapshot.trajectory}</div>
              <div className="text-[11px] text-slate-500">Risk Delta: {snapshot.risk_delta > 0 ? `+${snapshot.risk_delta}` : snapshot.risk_delta}</div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
              <div className="text-xs text-slate-400">Transaction Velocity</div>
              <div className="text-2xl font-bold text-emerald-400">{snapshot.velocity.tx_velocity_per_hour} / hr</div>
              <div className="text-[11px] text-slate-500">Exposure: +${snapshot.exposure_delta.toLocaleString()}</div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
              <div className="text-xs text-slate-400">New Account Flow</div>
              <div className="text-2xl font-bold text-purple-400">{snapshot.velocity.account_velocity_per_hour} / hr</div>
              <div className="text-[11px] text-slate-500">Counterparties: {snapshot.velocity.counterparty_velocity_per_hour}/hr</div>
            </div>
          </div>

          {/* Predictive Forecast Horizons */}
          {forecast && (
            <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Clock className="h-4 w-4" /> Predictive Risk Projections (Next 1h to 7d)
                </span>
                <span className="text-xs text-slate-400">Status: {forecast.status}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {Object.entries(forecast.horizons).map(([key, h]) => (
                  <div key={key} className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-300">{h.horizon}</span>
                      <span className="font-bold text-amber-400">{h.forecast_score ?? 'N/A'}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">Trend: {h.trend}</div>
                    <div className="text-[10px] text-slate-500">Conf: {Math.round(h.confidence * 100)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 text-rose-400">Snapshot data unavailable.</div>
      )}
    </div>
  );
};
