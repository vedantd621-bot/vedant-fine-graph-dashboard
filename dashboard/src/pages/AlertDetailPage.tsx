import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ShieldAlert,
  CheckCircle2,
  Clock,
  XCircle,
  ExternalLink,
  DollarSign,
  Users,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { AlertDetail, AlertStatus, GraphPayload } from '../types';
import { InteractiveGraph } from '../components/graph/InteractiveGraph';

interface AlertDetailPageProps {
  alertId: string;
  onBack: () => void;
  onSelectAccount: (accountId: string) => void;
}

export const AlertDetailPage: React.FC<AlertDetailPageProps> = ({
  alertId,
  onBack,
  onSelectAccount,
}) => {
  const [alert, setAlert] = useState<AlertDetail | null>(null);
  const [graphData, setGraphData] = useState<GraphPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [updating, setUpdating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlertData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getAlertDetail(alertId);
      setAlert(data);
      if (data.primary_account) {
        const gData = await apiClient.getAccountGraph(data.primary_account, 2);
        setGraphData(gData);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load alert details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertData();
  }, [alertId]);

  const handleStatusUpdate = async (newStatus: AlertStatus) => {
    try {
      setUpdating(true);
      const updated = await apiClient.updateAlertStatus(alertId, newStatus);
      setAlert(updated);
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <span>Loading alert dossier...</span>
      </div>
    );
  }

  if (error || !alert) {
    return (
      <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
        <p>{error || 'Alert not found.'}</p>
        <button onClick={onBack} className="mt-3 text-xs underline">
          Back to Alerts
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Alerts
        </button>

        {/* Status Action Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 mr-1">Status:</span>
          {alert.status !== 'INVESTIGATING' && (
            <button
              disabled={updating}
              onClick={() => handleStatusUpdate('INVESTIGATING')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border border-amber-500/30 text-xs font-semibold transition-colors"
            >
              <Clock className="h-3.5 w-3.5" /> Mark Investigating
            </button>
          )}
          {alert.status !== 'RESOLVED' && (
            <button
              disabled={updating}
              onClick={() => handleStatusUpdate('RESOLVED')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 text-xs font-semibold transition-colors"
            >
              <CheckCircle2 className="h-3.5 w-3.5" /> Resolve Alert
            </button>
          )}
          {alert.status !== 'DISMISSED' && (
            <button
              disabled={updating}
              onClick={() => handleStatusUpdate('DISMISSED')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 text-xs font-semibold transition-colors"
            >
              <XCircle className="h-3.5 w-3.5" /> Dismiss
            </button>
          )}
        </div>
      </div>

      {/* Alert Banner Dossier */}
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm font-bold text-cyan-400">{alert.alert_id}</span>
              <span className="text-xs font-bold uppercase px-2.5 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {alert.severity} SEVERITY
              </span>
              <span className="text-xs font-bold uppercase px-2.5 py-0.5 rounded bg-slate-800 text-slate-300">
                STATUS: {alert.status}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 mt-2">{alert.description}</h2>
          </div>

          <div className="text-right">
            <div className="text-xs text-slate-400">Primary Account</div>
            <button
              onClick={() => onSelectAccount(alert.primary_account)}
              className="text-base font-bold text-cyan-400 hover:underline flex items-center gap-1 ml-auto"
            >
              {alert.primary_account} <ExternalLink className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Forensic Evidence Breakdown */}
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Forensic Pattern Evidence
          </div>
          <p className="text-sm text-slate-200">{alert.evidence.reason_summary}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 text-xs">
            <div>
              <span className="text-slate-400">Metric:</span>{' '}
              <span className="font-semibold text-slate-200">{alert.evidence.metric_name}</span>
            </div>
            <div>
              <span className="text-slate-400">Observed Value:</span>{' '}
              <span className="font-semibold text-cyan-400">{String(alert.evidence.metric_value)}</span>
            </div>
            <div>
              <span className="text-slate-400">Threshold:</span>{' '}
              <span className="font-semibold text-slate-200">{String(alert.evidence.threshold_value)}</span>
            </div>
            <div>
              <span className="text-slate-400">Confidence:</span>{' '}
              <span className="font-semibold text-emerald-400">{(alert.confidence * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Explainable Reasons */}
        {alert.reasons && alert.reasons.length > 0 && (
          <div className="space-y-1.5 pt-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Risk Justifications
            </div>
            <ul className="space-y-1 text-xs text-slate-300">
              {alert.reasons.map((rsn, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  <span>{rsn}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Related Accounts & Transactions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
            <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-cyan-400" />
              <span>Related Syndicate Accounts ({alert.related_accounts.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {alert.related_accounts.map((accId) => (
                <button
                  key={accId}
                  onClick={() => onSelectAccount(accId)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 transition-colors"
                >
                  {accId}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
            <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <DollarSign className="h-3.5 w-3.5 text-emerald-400" />
              <span>Involved Transactions ({alert.transaction_ids.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {alert.transaction_ids.map((txId) => (
                <span
                  key={txId}
                  className="px-2 py-0.5 rounded bg-slate-800 text-xs font-mono text-slate-300"
                >
                  {txId}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Subgraph Investigation Visualizer */}
      {graphData && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200">
              Interactive Syndicate Subgraph Neighborhood
            </h3>
            <span className="text-xs text-slate-400">Click any account node to navigate</span>
          </div>
          <InteractiveGraph
            data={graphData}
            focalAccountId={alert.primary_account}
            onSelectNode={onSelectAccount}
            height={480}
          />
        </div>
      )}
    </div>
  );
};
