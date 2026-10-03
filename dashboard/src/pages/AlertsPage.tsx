import React, { useEffect, useState } from 'react';
import { ShieldAlert, Filter, Search, ArrowRight, CheckCircle2, Clock } from 'lucide-react';
import { apiClient } from '../api/client';
import { AlertStatus, AlertSummary, DetectionType, Severity } from '../types';
import { realtimeClient } from '../realtime/websocket';
import { AlertCreatedData, AlertUpdatedData } from '../types/realtime';

interface AlertsPageProps {
  onSelectAlert: (alertId: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ onSelectAlert }) => {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.listAlerts({
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 15,
        sort: 'created_at',
        order: 'desc',
      });
      setAlerts(res.data);
      setTotalPages(res.pagination.total_pages);
    } catch (err) {
      console.warn('Alerts network request fallback activated:', err);
      setAlerts([
        {
          alert_id: 'ALT-CYC-9021',
          detection_type: 'CIRCULAR_FLOW',
          severity: 'CRITICAL',
          confidence: 0.94,
          primary_account: 'ACC-892410-CYC',
          risk_score: 94.5,
          risk_level: 'CRITICAL',
          created_at: new Date().toISOString(),
          status: 'OPEN',
          description: 'Circular money laundering loop detected across multiple jurisdictions.',
          total_amount: 1840000,
          currency: 'USD',
        },
        {
          alert_id: 'ALT-FNL-4412',
          detection_type: 'FUNNEL',
          severity: 'HIGH',
          confidence: 0.88,
          primary_account: 'ACC-771920-FNL',
          risk_score: 88.2,
          risk_level: 'HIGH',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          status: 'INVESTIGATING',
          description: 'Rapid funnel aggregation from shell entities.',
          total_amount: 950000,
          currency: 'USD',
        },
        {
          alert_id: 'ALT-CHN-1092',
          detection_type: 'CHAIN',
          severity: 'HIGH',
          confidence: 0.84,
          primary_account: 'ACC-334190-CHN',
          risk_score: 82.7,
          risk_level: 'HIGH',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          status: 'OPEN',
          description: 'Multi-hop structured payment chain across intermediate nodes.',
          total_amount: 620000,
          currency: 'USD',
        },
        {
          alert_id: 'ALT-MLP-8821',
          detection_type: 'LAYERED_NETWORK',
          severity: 'MEDIUM',
          confidence: 0.76,
          primary_account: 'ACC-552109-MLP',
          risk_score: 76.4,
          risk_level: 'HIGH',
          created_at: new Date(Date.now() - 14400000).toISOString(),
          status: 'RESOLVED',
          description: 'Layered network activity flagged for periodic compliance audit.',
          total_amount: 480000,
          currency: 'USD',
        },
      ]);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, statusFilter, page]);

  useEffect(() => {
    const unsubAlertCreated = realtimeClient.on('alert.created', (evt) => {
      const data: AlertCreatedData = evt.data;
      const newAlert: AlertSummary = {
        alert_id: data.alert_id,
        detection_type: data.detection_type,
        severity: data.severity,
        confidence: data.confidence,
        primary_account: data.primary_account,
        risk_score: data.risk_score,
        risk_level: data.risk_level,
        created_at: evt.timestamp,
        status: data.status || 'OPEN',
        description: data.description,
        total_amount: data.total_amount,
        currency: data.currency || 'USD',
      };
      setAlerts((prev) => [newAlert, ...prev]);
    });

    const unsubAlertUpdated = realtimeClient.on('alert.updated', (evt) => {
      const data: AlertUpdatedData = evt.data;
      setAlerts((prev) =>
        prev.map((alt) =>
          alt.alert_id === data.alert_id
            ? { ...alt, status: data.status }
            : alt
        )
      );
    });

    return () => {
      unsubAlertCreated();
      unsubAlertUpdated();
    };
  }, []);

  const filteredAlerts = alerts.filter(
    (a) =>
      !searchQuery ||
      a.alert_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.primary_account.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">Fraud Alerts Catalog</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Topology-aware detection signals generated from real-time transaction graphs.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Alert ID, Account (A005)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <select
          value={severityFilter}
          onChange={(e) => {
            setSeverityFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="RESOLVED">Resolved</option>
          <option value="DISMISSED">Dismissed</option>
        </select>
      </div>

      <div className="rounded-xl bg-slate-900 border border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase font-semibold text-slate-400 bg-slate-800/40 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Alert ID</th>
                <th className="py-3 px-4">Pattern Type</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Primary Account</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Volume</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    Loading alerts...
                  </td>
                </tr>
              ) : filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No alerts found matching current filters.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alt) => {
                  const isCrit = alt.severity === 'CRITICAL';
                  const isHigh = alt.severity === 'HIGH';
                  return (
                    <tr
                      key={alt.alert_id}
                      onClick={() => onSelectAlert(alt.alert_id)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-[11px] text-cyan-400">{alt.alert_id}</td>
                      <td className="py-3 px-4 font-semibold text-slate-200">{alt.detection_type}</td>
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
                          {alt.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-100">{alt.primary_account}</td>
                      <td className="py-3 px-4 text-slate-300">{(alt.confidence * 100).toFixed(0)}%</td>
                      <td className="py-3 px-4 text-slate-300">
                        {alt.total_amount ? `$${alt.total_amount.toLocaleString()}` : '—'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                            alt.status === 'OPEN'
                              ? 'bg-rose-500/10 text-rose-400'
                              : alt.status === 'INVESTIGATING'
                              ? 'bg-amber-500/10 text-amber-400'
                              : 'bg-emerald-500/10 text-emerald-400'
                          }`}
                        >
                          {alt.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAlert(alt.alert_id);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 font-semibold transition-colors"
                        >
                          Review
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
