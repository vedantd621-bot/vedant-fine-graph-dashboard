import React, { useState } from 'react';
import { CorrelationGroup } from '../types';
import { apiService } from '../api/client';

export const AlertCorrelationPage: React.FC = () => {
  const [alertId, setAlertId] = useState<string>('ALT-CIRC-01');
  const [correlation, setCorrelation] = useState<CorrelationGroup | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleCorrelate = async () => {
    if (!alertId.trim()) return;
    try {
      setLoading(true);
      const res = await apiService.getAlertCorrelation(alertId.trim());
      setCorrelation(res.data);
    } catch (err) {
      console.error('Correlation query failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
            🔗
          </span>
          Cross-Alert Correlation & Attribution Explorer
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Uncover explainable relationships between distinct alerts across shared accounts, devices, IPs, and temporal clusters.
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
        <div className="flex gap-4">
          <input
            type="text"
            value={alertId}
            onChange={(e) => setAlertId(e.target.value)}
            placeholder="Target Alert ID (e.g. ALT-CIRC-01)"
            className="flex-grow bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono outline-none"
          />
          <button
            onClick={handleCorrelate}
            disabled={loading}
            className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm rounded-lg transition"
          >
            {loading ? 'Correlating...' : 'Analyze Correlation'}
          </button>
        </div>
      </div>

      {correlation && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase text-slate-400">Correlation Strength</div>
              <div className="text-3xl font-black text-sky-400 mt-1">
                {(correlation.correlation_score * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-slate-500 mt-1">Multi-signal confidence</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase text-slate-400">Primary Alert</div>
              <div className="text-xl font-bold font-mono text-white mt-2">{correlation.primary_alert_id}</div>
              <div className="text-xs text-slate-500 mt-1">Origin alert seed</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase text-slate-400">Correlated Alerts</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1.5">{correlation.correlated_alert_ids.length} Alerts</div>
              <div className="text-xs text-slate-500 mt-1">Linked incidents</div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <h3 className="text-base font-bold text-white">Explainable Correlation Attribution</h3>
            <p className="text-sm text-slate-300">{correlation.explanation}</p>
            <div className="flex flex-wrap gap-2 pt-2">
              {correlation.reasons.map((r, i) => (
                <span key={i} className="px-2.5 py-1 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-md text-xs font-semibold">
                  ✓ {r}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertCorrelationPage;
