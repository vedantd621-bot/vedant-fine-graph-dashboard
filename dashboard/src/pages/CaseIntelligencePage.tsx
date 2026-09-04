import React, { useState, useEffect } from 'react';
import {
  Share2,
  RefreshCw,
  Link2,
  ShieldAlert,
  ArrowRight,
  Info,
  CheckCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  CaseCorrelation,
  CaseRelationshipGraph,
  EvidenceProvenance,
  InvestigationCaseSummary,
} from '../types';

interface CaseIntelligencePageProps {
  onSelectCase?: (caseId: string) => void;
}

export const CaseIntelligencePage: React.FC<CaseIntelligencePageProps> = ({ onSelectCase }) => {
  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-2026-001');
  const [correlations, setCorrelations] = useState<CaseCorrelation[]>([]);
  const [graph, setGraph] = useState<CaseRelationshipGraph | null>(null);
  const [provenance, setProvenance] = useState<EvidenceProvenance[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async (cid: string) => {
    try {
      setLoading(true);
      const [casesRes, corrRes, graphRes, provRes] = await Promise.all([
        apiClient.listCases(),
        apiClient.getCaseCorrelations(cid).catch(() => ({ data: { correlations: [] } })),
        apiClient.getCaseRelationshipGraph(cid).catch(() => ({ data: null })),
        apiClient.getCaseEvidenceProvenance(cid).catch(() => ({ data: { records: [] } })),
      ]);

      setCases(casesRes.data);
      setCorrelations(corrRes.data.correlations || []);
      setGraph(graphRes.data);
      setProvenance(provRes.data.records || []);
    } catch (err) {
      console.error('Failed to load case intelligence:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedCaseId);
  }, [selectedCaseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Share2 className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">Cross-Case Intelligence & Relationship Graph</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic multi-signal correlation matching shared accounts, detectors, flow, and evidence provenance
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} — {c.title}
              </option>
            ))}
          </select>
          <button
            onClick={() => loadData(selectedCaseId)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading case relationships...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Correlated Cases List */}
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Correlated Cases ({correlations.length})
              </span>
              <Link2 className="h-4 w-4 text-cyan-400" />
            </div>

            <div className="divide-y divide-slate-800 space-y-2">
              {correlations.map((c) => (
                <div key={c.correlation_id} className="pt-2 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{c.case_b}</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold text-[10px]">
                      {Math.round(c.signal_strength * 100)}% Match
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{c.explanation}</p>
                  <div className="flex items-center gap-1 text-[10px] text-cyan-400/80">
                    <span>Signal: {c.signal_type}</span>
                  </div>
                </div>
              ))}
              {correlations.length === 0 && (
                <div className="py-4 text-xs text-slate-500 italic">No strong correlation links discovered.</div>
              )}
            </div>
          </div>

          {/* Relationship Graph Summary Card */}
          <div className="lg:col-span-2 p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Case Topology Graph Structure
              </span>
              <span className="text-xs text-slate-400">
                {graph ? `${graph.total_nodes} Nodes, ${graph.total_edges} Edges` : ''}
              </span>
            </div>

            {graph ? (
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-3">
                <div className="text-xs text-slate-300 font-semibold">Graph Nodes Breakdown:</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  {['CASE', 'ACCOUNT', 'ALERT', 'EVIDENCE'].map((type) => {
                    const count = graph.nodes.filter((n) => n.type === type).length;
                    return (
                      <div key={type} className="p-2 bg-slate-900 rounded border border-slate-800">
                        <div className="text-[10px] text-slate-400 font-bold">{type}</div>
                        <div className="text-lg font-bold text-slate-100">{count}</div>
                      </div>
                    );
                  })}
                </div>

                <div className="pt-2 text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Focal Node: </span>
                  {graph.focal_case_id}
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500">No graph data available.</div>
            )}

            {/* Evidence Provenance Table */}
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Evidence Provenance Tracing ({provenance.length})
              </span>
              <div className="space-y-1 text-xs">
                {provenance.map((p) => (
                  <div
                    key={p.provenance_id}
                    className="p-2 bg-slate-950 rounded border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{p.derived_factor || p.evidence_id}</span>
                      <span className="text-[11px] text-slate-400 ml-2">({p.source_type} → {p.target_type})</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      {p.relationship_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
