import React, { useState, useEffect } from 'react';
import {
  Layers,
  RefreshCw,
  Share2,
  AlertTriangle,
  ArrowRight,
  Info,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { DiscoveredPattern, PatternSimilarityResponse } from '../types';

export const PatternIntelligencePage: React.FC = () => {
  const [patterns, setPatterns] = useState<DiscoveredPattern[]>([]);
  const [selectedPatternId, setSelectedPatternId] = useState<string | null>('PAT-CIRCULAR-01');
  const [similar, setSimilar] = useState<PatternSimilarityResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await apiClient.listDiscoveredPatterns();
      setPatterns(res.data);
      if (res.data.length > 0) {
        const pId = selectedPatternId || res.data[0].pattern_id;
        setSelectedPatternId(pId);
        const simRes = await apiClient.getSimilarPatterns(pId).catch(() => ({ data: [] }));
        setSimilar(simRes.data);
      }
    } catch (err) {
      console.error('Failed to load pattern intelligence:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedPatternId]);

  const selectedPattern = patterns.find((p) => p.pattern_id === selectedPatternId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <Layers className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">Recurring Fraud Pattern Intelligence</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Topological motif discovery, frequency tracking, and explainable multi-signal pattern similarity
          </p>
        </div>
        <button
          onClick={loadData}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Extracting graph motifs...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pattern Catalog */}
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Discovered Motifs ({patterns.length})
            </span>
            <div className="divide-y divide-slate-800 text-xs space-y-2">
              {patterns.map((p) => (
                <div
                  key={p.pattern_id}
                  onClick={() => setSelectedPatternId(p.pattern_id)}
                  className={`pt-2 p-2 rounded cursor-pointer transition-colors ${
                    selectedPatternId === p.pattern_id ? 'bg-purple-500/10 border border-purple-500/30' : 'hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-100">{p.name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300">
                      {p.risk_score} Risk
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-1">
                    <span>Freq: {p.frequency}x</span>
                    <span>•</span>
                    <span>Exposure: ${p.financial_exposure.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pattern Dossier & Similar Motifs */}
          <div className="lg:col-span-2 space-y-4">
            {selectedPattern && (
              <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-100">{selectedPattern.name}</span>
                  <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {selectedPattern.pattern_type}
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed">{selectedPattern.explanation}</p>

                <div className="pt-2 border-t border-slate-800 space-y-1 text-slate-400">
                  <div className="font-semibold text-slate-300">Supporting Graph Signals:</div>
                  {selectedPattern.supporting_signals.map((s, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-slate-300">
                      <span>•</span>
                      <span>{s}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center gap-4 text-slate-400">
                  <span>Linked Cases: {selectedPattern.related_cases.join(', ') || 'None'}</span>
                  <span>•</span>
                  <span>Linked Campaigns: {selectedPattern.related_campaigns.join(', ') || 'None'}</span>
                </div>
              </div>
            )}

            {/* Pattern Similarity */}
            <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3 text-xs">
              <span className="font-bold uppercase tracking-wider text-slate-300">
                Structural Pattern Similarity Comparison
              </span>
              <div className="space-y-2">
                {similar.map((sim, i) => (
                  <div key={i} className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Comparison with {sim.pattern_b}</span>
                      <span className="font-bold text-cyan-400">{Math.round(sim.similarity_score * 100)}% Similarity</span>
                    </div>
                    <p className="text-slate-400">{sim.explanation}</p>
                  </div>
                ))}
                {similar.length === 0 && (
                  <div className="text-slate-500 italic">No secondary patterns available for similarity comparison.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
