import React, { useState } from 'react';
import { ThreatPropagationAnalysis } from '../types';
import { apiService } from '../api/client';

export const ThreatPropagationPage: React.FC = () => {
  const [entityId, setEntityId] = useState<string>('acc_881');
  const [maxHops, setMaxHops] = useState<number>(3);
  const [timeWindowHours, setTimeWindowHours] = useState<number>(24);
  const [analysis, setAnalysis] = useState<ThreatPropagationAnalysis | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!entityId.trim()) return;
    try {
      setLoading(true);
      setError(null);
      const res = await apiService.analyzeThreatPropagation({
        origin_entity_id: entityId.trim(),
        max_hops: maxHops,
        time_window_hours: timeWindowHours,
      });
      setAnalysis(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Threat propagation analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="p-2 bg-rose-500/10 text-rose-400 rounded-lg border border-rose-500/20">
            🕸️
          </span>
          Multi-Hop Threat Propagation Explorer
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Simulate graph contagion pathways, compute deterministic 6-factor propagation scores, and trigger containment recommendations.
        </p>
      </div>

      {/* Origin Entity Controls */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Origin Entity ID / Account
            </label>
            <input
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              placeholder="e.g. acc_881, acc_mule_44"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:border-rose-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Max Hops (1 - 5)
            </label>
            <select
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-rose-500 outline-none"
            >
              <option value={1}>1 Hop (Direct Counterparties)</option>
              <option value={2}>2 Hops (Intermediaries)</option>
              <option value={3}>3 Hops (Layered Network)</option>
              <option value={4}>4 Hops (Extended Perimeter)</option>
              <option value={5}>5 Hops (Ecosystem Contagion)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-lg text-sm transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  <span>Modeling Contagion...</span>
                </>
              ) : (
                <>
                  <span>⚡</span> Execute Propagation Analysis
                </>
              )}
            </button>
          </div>
        </div>
        {error && <div className="text-xs text-rose-400 bg-rose-950/40 p-2.5 rounded border border-rose-800">{error}</div>}
      </div>

      {analysis && (
        <div className="space-y-6">
          {/* Analysis Summary Scoreboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Propagation Score</div>
              <div className={`text-3xl font-black mt-2 ${analysis.propagation_score >= 75 ? 'text-rose-400' : 'text-amber-400'}`}>
                {analysis.propagation_score} <span className="text-xs font-normal text-slate-500">/ 100</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">6-factor deterministic index</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Affected Entities</div>
              <div className="text-3xl font-bold text-sky-400 mt-2">{analysis.total_affected_entities}</div>
              <div className="text-xs text-slate-500 mt-1">Across {analysis.max_hops} hops</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Financial Exposure</div>
              <div className="text-3xl font-bold text-emerald-400 mt-2">
                ${analysis.total_financial_exposure.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">Cumulative contagion volume</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Risk Velocity</div>
              <div className="text-3xl font-bold text-amber-400 mt-2">
                ${analysis.risk_velocity.toLocaleString()}
                <span className="text-xs font-normal text-slate-500">/min</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">Transmission rate</div>
            </div>
          </div>

          {/* Interactive Topology Graph Visualizer */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>🗺️ Contagion Topology Matrix</span>
              <span className="text-xs font-mono text-slate-400">{analysis.topology.nodes.length} Nodes / {analysis.topology.edges.length} Links</span>
            </h3>
            
            <div className="h-64 bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden flex items-center justify-center">
              <svg className="w-full h-full p-4">
                {/* Render Edges */}
                {analysis.topology.edges.map((e, idx) => {
                  const sNodeIdx = analysis.topology.nodes.findIndex(n => n.id === e.source);
                  const tNodeIdx = analysis.topology.nodes.findIndex(n => n.id === e.target);
                  const x1 = 100 + (sNodeIdx % 4) * 220;
                  const y1 = 60 + Math.floor(sNodeIdx / 4) * 110;
                  const x2 = 100 + (tNodeIdx % 4) * 220;
                  const y2 = 60 + Math.floor(tNodeIdx / 4) * 110;
                  return (
                    <line
                      key={idx}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#f43f5e"
                      strokeWidth={2}
                      strokeDasharray="4"
                      strokeOpacity={0.7}
                    />
                  );
                })}
                {/* Render Nodes */}
                {analysis.topology.nodes.map((node, idx) => {
                  const cx = 100 + (idx % 4) * 220;
                  const cy = 60 + Math.floor(idx / 4) * 110;
                  const isOrigin = node.hop === 0;
                  return (
                    <g key={node.id} className="cursor-pointer">
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isOrigin ? 22 : 16}
                        fill={isOrigin ? '#e11d48' : node.risk > 75 ? '#ea580c' : '#3b82f6'}
                        stroke="#ffffff"
                        strokeWidth={isOrigin ? 3 : 1.5}
                        fillOpacity={0.9}
                      />
                      <text
                        x={cx}
                        y={cy + 30}
                        textAnchor="middle"
                        fill="#cbd5e1"
                        fontSize={10}
                        fontFamily="monospace"
                      >
                        {node.id} (Hop {node.hop})
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Step Timeline */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-base font-bold text-white">Chronological Threat Expansion Timeline</h3>
            <div className="space-y-3">
              {analysis.steps.map((step) => (
                <div key={step.step_index} className="flex gap-4 items-start bg-slate-950 p-3.5 rounded-lg border border-slate-800">
                  <div className="flex-shrink-0 w-16 text-center">
                    <span className="px-2 py-1 bg-rose-500/10 text-rose-400 rounded font-mono font-bold text-xs border border-rose-500/20">
                      T+{step.step_time_offset_sec}s
                    </span>
                  </div>
                  <div className="flex-grow space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">
                        Step {step.step_index}: {step.mechanism}
                      </span>
                      <span className="text-xs font-bold text-emerald-400">
                        +${step.new_exposure_amount.toLocaleString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{step.description}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {step.reached_entities.map((ent) => (
                        <span key={ent} className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-900 text-slate-300 rounded border border-slate-800">
                          {ent}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Containment Recommendations */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>🛡️</span> Automated Containment Recommendations
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {analysis.containment_recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs text-slate-300">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreatPropagationPage;
