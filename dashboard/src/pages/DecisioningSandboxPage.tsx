import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  History,
  FileCheck
} from 'lucide-react';
import { FraudDecision, DecisionOverride, DecisionVerdict, SimulationResult } from '../types/enterprise';

export const DecisioningSandboxPage: React.FC = () => {
  const [decisions, setDecisions] = useState<FraudDecision[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<FraudDecision | null>(null);
  const [overrides, setOverrides] = useState<DecisionOverride[]>([]);
  const [overrideVerdict, setOverrideVerdict] = useState<DecisionVerdict>('REVIEW');
  const [overrideReason, setOverrideReason] = useState('');
  
  // Simulation State
  const [scenarioName, setScenarioName] = useState('Stress Test Risk Threshold');
  const [riskWeightDelta, setRiskWeightDelta] = useState(15);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [simulating, setSimulating] = useState(false);

  const apiBase = (process.env.REACT_APP_API_BASE_URL) || 'http://localhost:8000';

  const fetchDecisions = async () => {
    try {
      const token = localStorage.getItem('fingraph_token') || localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/decisioning/?limit=20`, { headers });
      if (res.ok) {
        const data = await res.json();
        setDecisions(data);
        if (data.length > 0 && !selectedDecision) {
          setSelectedDecision(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch decisions:', err);
    }
  };

  useEffect(() => {
    fetchDecisions();
  }, []);

  const handleApplyOverride = async () => {
    if (!selectedDecision || !overrideReason) return;
    try {
      const token = localStorage.getItem('fingraph_token') || localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/decisioning/${selectedDecision.decision_id}/override`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          override_verdict: overrideVerdict,
          reason: overrideReason,
          evidence_references: ['manual_auditor_review'],
        }),
      });

      if (res.ok) {
        setOverrideReason('');
        await fetchDecisions();
      }
    } catch (err) {
      console.error('Failed to submit override:', err);
    }
  };

  const handleRunSimulation = async () => {
    setSimulating(true);
    try {
      const token = localStorage.getItem('fingraph_token') || localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/decisioning/simulate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          scenario_name: scenarioName,
          description: 'Evaluating impact of parameter delta',
          parameters: [
            {
              name: 'risk_threshold',
              current_value: 50,
              hypothetical_value: 50 + riskWeightDelta,
            }
          ],
          alert_ids: ['alt_001', 'alt_002', 'alt_003'],
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSimulationResult(data);
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800 backdrop-blur flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <ShieldAlert className="w-7 h-7 text-emerald-400" />
            Fraud Decisioning & Simulation Sandbox
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Inspect deterministic decisions, record human-in-the-loop overrides, and run non-mutating What-If simulations.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Decisions List */}
        <div className="bg-gray-900/60 p-5 rounded-xl border border-gray-800 space-y-3">
          <h3 className="text-base font-bold text-white">Active Decisions</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {decisions.map((d) => (
              <div
                key={d.decision_id}
                onClick={() => setSelectedDecision(d)}
                className={`p-3.5 rounded-lg border cursor-pointer transition ${
                  selectedDecision?.decision_id === d.decision_id
                    ? 'bg-emerald-950/30 border-emerald-500/50'
                    : 'bg-gray-800/40 border-gray-800 hover:bg-gray-800/70'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="text-xs font-mono text-gray-400">{d.decision_id}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      d.verdict === 'BLOCK'
                        ? 'bg-red-500/20 text-red-300'
                        : d.verdict === 'ESCALATE'
                        ? 'bg-amber-500/20 text-amber-300'
                        : d.verdict === 'REVIEW'
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-green-500/20 text-green-300'
                    }`}
                  >
                    {d.verdict}
                  </span>
                </div>
                <div className="text-sm font-semibold text-white mt-1">Risk Score: {d.risk_score}</div>
                <div className="text-xs text-gray-400 truncate mt-0.5">{d.evidence_summary}</div>
                {d.is_override && (
                  <span className="inline-block text-[10px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded mt-2">
                    Human Override Applied
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Center: Detail & Override Console */}
        <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800 space-y-5">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-emerald-400" />
            Decision Details & Override Gate
          </h3>
          {selectedDecision ? (
            <div className="space-y-4 text-sm">
              <div className="bg-gray-800/40 p-4 rounded-lg border border-gray-800 space-y-2">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>CONFIDENCE: {selectedDecision.confidence}</span>
                  <span>POLICY: {selectedDecision.policy_version || 'v1.0'}</span>
                </div>
                <div className="text-white font-semibold">Recommendation:</div>
                <div className="text-gray-300 text-xs">{selectedDecision.recommendation}</div>
                <div className="text-xs text-gray-400 pt-2">Contributing Signals:</div>
                <div className="flex flex-wrap gap-1">
                  {selectedDecision.contributing_signals.map((s, idx) => (
                    <span key={idx} className="text-[10px] bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* Human Override Action */}
              <div className="p-4 bg-gray-800/30 rounded-lg border border-gray-700/50 space-y-3">
                <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                  Human-in-the-Loop Override
                </h4>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">NEW VERDICT</label>
                  <select
                    value={overrideVerdict}
                    onChange={(e) => setOverrideVerdict(e.target.value as DecisionVerdict)}
                    className="w-full bg-gray-800 border border-gray-700 text-white rounded p-2 text-xs"
                  >
                    {(['ALLOW', 'REVIEW', 'ESCALATE', 'BLOCK', 'CONFIRM_FRAUD', 'FALSE_POSITIVE'] as const).map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">OVERRIDE JUSTIFICATION</label>
                  <textarea
                    rows={2}
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    placeholder="Enter compliance rationale..."
                    className="w-full bg-gray-800 border border-gray-700 text-white rounded p-2 text-xs"
                  />
                </div>
                <button
                  onClick={handleApplyOverride}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded text-xs transition"
                >
                  Record Immutable Override
                </button>
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Select a decision to inspect.</p>
          )}
        </div>

        {/* Right: What-If Simulation Sandbox */}
        <div className="bg-gray-900/60 p-6 rounded-xl border border-gray-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            What-If Sandbox (Non-Mutating)
          </h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">SCENARIO NAME</label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded p-2 text-xs font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 flex justify-between mb-1">
                <span>THRESHOLD DELTA</span>
                <span className="text-indigo-300 font-mono">+{riskWeightDelta} pts</span>
              </label>
              <input
                type="range"
                min="-30"
                max="30"
                value={riskWeightDelta}
                onChange={(e) => setRiskWeightDelta(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <button
              onClick={handleRunSimulation}
              disabled={simulating}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded text-xs transition flex items-center justify-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5" /> Run Simulation
            </button>

            {simulationResult && (
              <div className="p-4 bg-indigo-950/20 border border-indigo-900/40 rounded-lg space-y-2 mt-4 text-xs">
                <div className="flex justify-between font-bold text-indigo-300">
                  <span>PREDICTED DELTA</span>
                  <span className="text-green-400">Sandbox Verified</span>
                </div>
                <div className="text-gray-300">
                  Alerts Impacted: <span className="font-mono text-white">{simulationResult.predicted_alerts_changed}</span>
                </div>
                <div className="text-gray-300">
                  Risk Score Shift: <span className="font-mono text-white">{simulationResult.predicted_risk_change}</span>
                </div>
                <div className="text-gray-300">
                  Exposure Shift: <span className="font-mono text-white">${simulationResult.predicted_exposure_change.toLocaleString()}</span>
                </div>
                <div className="pt-2 text-[11px] text-gray-400 border-t border-gray-800">
                  {simulationResult.recommendation_changes[0]}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
export default DecisioningSandboxPage;
