import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Plus,
  ShieldCheck,
  Clock,
  CheckCircle2,
  Calendar,
  Layers,
  RefreshCw
} from 'lucide-react';
import { ReportSnapshot, ReportType, ReportFormat } from '../types/enterprise';

const REPORT_TYPES: { type: ReportType; label: string; desc: string }[] = [
  { type: 'EXECUTIVE_FRAUD_REPORT', label: 'Executive Fraud Report', desc: 'High-level posture, loss prevention, and executive summaries.' },
  { type: 'FRAUD_NETWORK_REPORT', label: 'Fraud Network Dossier', desc: 'Syndicate topology, Louvain clusters, and high-risk originators.' },
  { type: 'CAMPAIGN_REPORT', label: 'Coordinated Campaign Report', desc: 'Multi-case campaign analysis and aggregated financial exposure.' },
  { type: 'INVESTIGATION_REPORT', label: 'Investigation Operations', desc: 'Triage SLA compliance, open cases, and investigator capacity.' },
  { type: 'DETECTOR_PERFORMANCE_REPORT', label: 'Detector Health & Drift', desc: 'Precision proxy, false-positive metrics, and Cypher rule drift.' },
  { type: 'OPERATIONS_REPORT', label: 'Operations & Workload', desc: 'Operational queue depth, investigator workload, and throughput.' },
  { type: 'RISK_REPORT', label: 'Entity Risk Score Matrix', desc: 'Distribution of entity scores across critical and high risk bands.' },
  { type: 'TENANT_POSTURE_REPORT', label: 'Tenant Governance Posture', desc: 'Multi-tenant isolation status and audit compliance verification.' },
];

export const ReportingCenterPage: React.FC = () => {
  const [snapshots, setSnapshots] = useState<ReportSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedType, setSelectedType] = useState<ReportType>('EXECUTIVE_FRAUD_REPORT');
  const [format, setFormat] = useState<ReportFormat>('JSON');

  const fetchSnapshots = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/reports/', { headers });
      if (res.ok) {
        const data = await res.json();
        setSnapshots(data);
      }
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/reports/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ report_type: selectedType, format }),
      });

      if (res.ok) {
        await fetchSnapshots();
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleExport = (reportId: string, exportFmt: ReportFormat) => {
    const token = localStorage.getItem('token');
    const url = `/api/v1/reports/${reportId}/export?format=${exportFmt}`;
    window.open(url, '_blank');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800 backdrop-blur flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <FileText className="w-7 h-7 text-indigo-400" />
            Enterprise Reporting Center
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Generate immutable cryptographic audit snapshots with spreadsheet formula injection protection.
          </p>
        </div>
        <button
          onClick={fetchSnapshots}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm border border-gray-700 transition"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Generator Console */}
      <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800 space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Plus className="w-5 h-5 text-indigo-400" />
          Generate New Audit Report
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="text-xs font-semibold text-gray-400 block mb-1">REPORT TYPE</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as ReportType)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-2.5 text-sm"
            >
              {REPORT_TYPES.map((t) => (
                <option key={t.type} value={t.type}>
                  {t.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {REPORT_TYPES.find((t) => t.type === selectedType)?.desc}
            </p>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-400 block mb-1">SNAPSHOT FORMAT</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFormat('JSON')}
                className={`flex-1 py-2.5 text-xs font-bold rounded-lg border transition ${
                  format === 'JSON'
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300'
                }`}
              >
                JSON (Schema)
              </button>
              <button
                type="button"
                onClick={() => setFormat('CSV')}
                className={`flex-1 py-2.5 text-xs font-bold rounded-lg border transition ${
                  format === 'CSV'
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300'
                }`}
              >
                CSV (Protected)
              </button>
            </div>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition flex items-center justify-center gap-2"
            >
              {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
              Compile Snapshot
            </button>
          </div>
        </div>
      </div>

      {/* Snapshot Archive */}
      <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          Immutable Snapshot Archive ({snapshots.length})
        </h3>
        {loading && snapshots.length === 0 ? (
          <p className="text-gray-400 text-sm">Loading archive...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 font-medium text-xs">
                  <th className="pb-3 px-3">REPORT ID</th>
                  <th className="pb-3 px-3">TITLE / TYPE</th>
                  <th className="pb-3 px-3">FORMAT</th>
                  <th className="pb-3 px-3">SHA-256 DIGEST</th>
                  <th className="pb-3 px-3">CREATED AT</th>
                  <th className="pb-3 px-3 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {snapshots.map((snap) => (
                  <tr key={snap.report_id} className="hover:bg-gray-800/30 transition">
                    <td className="py-3 px-3 text-indigo-300 font-mono text-xs">{snap.report_id}</td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-white">{snap.title}</div>
                      <div className="text-[11px] text-gray-400">{snap.report_type}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] px-2 py-0.5 bg-gray-800 text-gray-300 border border-gray-700 rounded font-mono">
                        {snap.format}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-gray-400 font-mono text-xs">
                      {snap.content_hash ? `${snap.content_hash.slice(0, 16)}...` : 'Pending'}
                    </td>
                    <td className="py-3 px-3 text-gray-400 text-xs">
                      {new Date(snap.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      <button
                        onClick={() => handleExport(snap.report_id, 'JSON')}
                        className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs rounded border border-gray-700 transition"
                      >
                        JSON
                      </button>
                      <button
                        onClick={() => handleExport(snap.report_id, 'CSV')}
                        className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs rounded border border-gray-700 transition"
                      >
                        CSV
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
export default ReportingCenterPage;
