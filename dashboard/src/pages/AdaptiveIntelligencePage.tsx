import React, { useEffect, useState } from 'react';
import {
  AutonomousIntelligenceSummary,
  DetectionGap,
  DetectorRecommendation,
  DetectorVersion,
  RiskCalibrationReport,
  ShadowSimulationResult,
} from '../types';
import { apiService } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export const AdaptiveIntelligencePage: React.FC = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState<AutonomousIntelligenceSummary | null>(null);
  const [gaps, setGaps] = useState<DetectionGap[]>([]);
  const [recommendations, setRecommendations] = useState<DetectorRecommendation[]>([]);
  const [versions, setVersions] = useState<DetectorVersion[]>([]);
  const [calibration, setCalibration] = useState<RiskCalibrationReport | null>(null);
  const [selectedGap, setSelectedGap] = useState<DetectionGap | null>(null);
  const [selectedRec, setSelectedRec] = useState<DetectorRecommendation | null>(null);
  const [shadowResult, setShadowResult] = useState<ShadowSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'gaps' | 'recommendations' | 'calibration' | 'versions'>('gaps');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const isAdmin = user?.role === 'admin';
  const isInvestigator = user?.role === 'investigator' || isAdmin;

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumRes, gapsRes, recsRes, versRes, calRes] = await Promise.all([
        apiService.getAutonomousSummary(),
        apiService.listDetectionGaps(),
        apiService.listDetectorRecommendations(),
        apiService.listDetectorVersions(),
        apiService.getRiskCalibrationReport(30),
      ]);
      setSummary(sumRes.data);
      setGaps(gapsRes.data);
      setRecommendations(recsRes.data);
      setVersions(versRes.data);
      setCalibration(calRes.data);
    } catch (err) {
      console.error('Failed to load autonomous intelligence data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScanGaps = async () => {
    try {
      setLoading(true);
      await apiService.triggerDetectionGapScan();
      await loadData();
    } catch (err) {
      console.error('Gap scan failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (recId: string, targetStatus: any) => {
    try {
      await apiService.reviewDetectorRecommendation(recId, {
        status: targetStatus,
        notes: reviewNotes || `Transitioned to ${targetStatus}`,
      });
      setReviewNotes('');
      setSelectedRec(null);
      await loadData();
    } catch (err: any) {
      alert(`Action failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleRunShadow = async (rec: DetectorRecommendation) => {
    try {
      setIsSimulating(true);
      const res = await apiService.runShadowSimulation({
        detector_id: rec.target_detector_id || 'det_custom',
        recommendation_id: rec.recommendation_id,
        parameters: rec.suggested_parameters,
        time_window_hours: 24,
      });
      setShadowResult(res.data);
    } catch (err) {
      console.error('Shadow simulation failed:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="p-8 text-center text-slate-400">
        <div className="animate-spin inline-block w-8 h-8 border-4 border-current border-t-transparent text-emerald-500 rounded-full" />
        <p className="mt-2">Loading Autonomous Fraud Intelligence Station...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
              ⚡
            </span>
            Autonomous Fraud Intelligence & Adaptive Detection
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Continuous detection gap analysis, human-in-the-loop adaptive tuning, and shadow detector validation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isInvestigator && (
            <button
              onClick={handleScanGaps}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition flex items-center gap-2"
            >
              <span>🔍</span> Scan Detection Gaps
            </button>
          )}
          <button
            onClick={loadData}
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium border border-slate-700"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Detection Gaps</div>
          <div className="text-2xl font-bold text-amber-400 mt-2">{summary?.active_gaps_count || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Uncovered graph motifs</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pending Proposals</div>
          <div className="text-2xl font-bold text-sky-400 mt-2">{summary?.pending_recommendations_count || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Awaiting review / approval</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Approved & Deployed</div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">{summary?.approved_recommendations_count || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Validated detector rules</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Version Registry</div>
          <div className="text-2xl font-bold text-indigo-400 mt-2">{summary?.active_detector_versions_count || 0}</div>
          <div className="text-xs text-slate-500 mt-1">Immutable rule versions</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('gaps')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'gaps' ? 'border-emerald-500 text-emerald-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Detection Gaps ({gaps.length})
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'recommendations' ? 'border-emerald-500 text-emerald-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Adaptive Recommendations ({recommendations.length})
        </button>
        <button
          onClick={() => setActiveTab('calibration')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'calibration' ? 'border-emerald-500 text-emerald-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Risk Score Calibration & Thresholds
        </button>
        <button
          onClick={() => setActiveTab('versions')}
          className={`pb-3 border-b-2 transition ${
            activeTab === 'versions' ? 'border-emerald-500 text-emerald-400 font-semibold' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Detector Version Registry ({versions.length})
        </button>
      </div>

      {/* TAB 1: Detection Gaps */}
      {activeTab === 'gaps' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gaps.map((gap) => (
              <div
                key={gap.gap_id}
                onClick={() => setSelectedGap(gap)}
                className={`p-5 rounded-xl border transition cursor-pointer ${
                  selectedGap?.gap_id === gap.gap_id
                    ? 'bg-slate-800/80 border-emerald-500 shadow-lg shadow-emerald-950/20'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {gap.gap_id}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-semibold ${
                      gap.priority === 'CRITICAL'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : gap.priority === 'HIGH'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}
                  >
                    {gap.priority}
                  </span>
                </div>
                <h3 className="font-semibold text-base text-white mt-2">{gap.title}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{gap.description}</p>
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Motifs: <strong className="text-slate-200">{gap.uncovered_motif_count}</strong></span>
                  <span>Exposure: <strong className="text-emerald-400">${gap.estimated_financial_exposure.toLocaleString()}</strong></span>
                  <span>Entities: <strong className="text-slate-200">{gap.affected_entities.length}</strong></span>
                </div>
              </div>
            ))}
          </div>

          {selectedGap && (
            <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-5 mt-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🔎</span> Gap Telemetry Details: {selectedGap.title}
                </h3>
                <button
                  onClick={() => setSelectedGap(null)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  ✕ Close
                </button>
              </div>
              <p className="text-sm text-slate-300">{selectedGap.description}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <div>Pattern Type: <span className="text-slate-200 font-mono">{selectedGap.pattern_type}</span></div>
                <div>Priority: <span className="text-amber-400 font-semibold">{selectedGap.priority}</span></div>
                <div>Exposure: <span className="text-emerald-400 font-bold">${selectedGap.estimated_financial_exposure.toLocaleString()}</span></div>
                <div>Status: <span className="text-sky-400 font-semibold">{selectedGap.status}</span></div>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Affected Entities</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedGap.affected_entities.map((e) => (
                    <span key={e} className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono text-xs">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
              {selectedGap.sample_motifs.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Sample Motifs</h4>
                  <pre className="p-3 bg-slate-950 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto border border-slate-800">
                    {JSON.stringify(selectedGap.sample_motifs, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Adaptive Recommendations */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {recommendations.map((rec) => (
              <div
                key={rec.recommendation_id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {rec.recommendation_id}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                      {rec.recommendation_type}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase ${
                      rec.status === 'DEPLOYED'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : rec.status === 'APPROVED'
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        : rec.status === 'UNDER_REVIEW'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : rec.status === 'REJECTED'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}
                  >
                    {rec.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white">{rec.title}</h3>
                  <p className="text-xs text-slate-300 mt-1">{rec.description}</p>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs space-y-1">
                  <div className="text-emerald-400 font-medium">Impact: {rec.expected_impact_summary}</div>
                  {rec.evidence_notes && <div className="text-slate-400">Evidence: {rec.evidence_notes}</div>}
                  {rec.target_detector_id && <div className="text-slate-500">Target Detector: <span className="font-mono text-slate-300">{rec.target_detector_id}</span></div>}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <button
                    onClick={() => handleRunShadow(rec)}
                    disabled={isSimulating}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-semibold rounded-lg border border-slate-700 transition"
                  >
                    🧪 {isSimulating ? 'Simulating...' : 'Run Shadow Simulation'}
                  </button>

                  {isInvestigator && rec.status !== 'DEPLOYED' && (
                    <div className="flex items-center gap-2">
                      {rec.status === 'PROPOSED' && (
                        <button
                          onClick={() => handleReview(rec.recommendation_id, 'UNDER_REVIEW')}
                          className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-semibold"
                        >
                          Mark Under Review
                        </button>
                      )}
                      {isAdmin && (rec.status === 'PROPOSED' || rec.status === 'UNDER_REVIEW') && (
                        <button
                          onClick={() => handleReview(rec.recommendation_id, 'APPROVED')}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold"
                        >
                          Approve
                        </button>
                      )}
                      {isAdmin && rec.status === 'APPROVED' && (
                        <button
                          onClick={() => handleReview(rec.recommendation_id, 'DEPLOYED')}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold"
                        >
                          Deploy to Production
                        </button>
                      )}
                      {rec.status !== 'REJECTED' && (
                        <button
                          onClick={() => handleReview(rec.recommendation_id, 'REJECTED')}
                          className="px-3 py-1 bg-rose-900/60 hover:bg-rose-800 text-rose-300 rounded text-xs font-semibold"
                        >
                          Reject
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Shadow Simulation Result Modal */}
          {shadowResult && (
            <div className="bg-slate-900 border border-sky-500/40 rounded-xl p-5 space-y-3 mt-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-sky-400 flex items-center gap-2">
                  <span>🧪</span> Shadow Detector Sandbox Simulation Results
                </h3>
                <button
                  onClick={() => setShadowResult(null)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  ✕ Close
                </button>
              </div>
              <p className="text-xs text-slate-300">{shadowResult.findings_summary}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div>Evaluated TX: <strong className="text-white">{shadowResult.transactions_evaluated_count.toLocaleString()}</strong></div>
                <div>Alerts Would Fire: <strong className="text-amber-400">{shadowResult.alerts_would_fire_count}</strong></div>
                <div>Novel Detections: <strong className="text-emerald-400">{shadowResult.novel_detections_count}</strong></div>
                <div>Estimated FPR: <strong className="text-sky-400">{(shadowResult.estimated_fpr * 100).toFixed(2)}%</strong></div>
                <div>Ground Truth: <span className="text-slate-300 font-mono text-[10px]">{shadowResult.ground_truth_status}</span></div>
                <div>Coverage: <strong className="text-emerald-400">{shadowResult.coverage_percentage}%</strong></div>
                <div>Execution Time: <strong className="text-slate-200">{shadowResult.execution_time_ms} ms</strong></div>
                <div>Window: <strong className="text-slate-200">{shadowResult.time_window_hours} Hours</strong></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Risk Calibration */}
      {activeTab === 'calibration' && calibration && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Empirical Risk Score vs Investigation Verdicts Matrix</h3>
                <p className="text-xs text-slate-400 mt-0.5">{calibration.calibration_notes}</p>
              </div>
              <span className="text-xs px-3 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Window: {calibration.evaluation_window_days} Days
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {calibration.buckets.map((b) => (
                <div key={b.bucket_id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center space-y-2">
                  <div className="text-xs font-mono font-bold text-slate-300 bg-slate-900 py-1 rounded">
                    Score {b.bucket_id}
                  </div>
                  <div className="text-xl font-black text-emerald-400">
                    {(b.confirmation_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-[11px] text-slate-400">Confirmation Rate</div>
                  <div className="pt-2 border-t border-slate-900 text-[10px] text-slate-500 space-y-0.5">
                    <div>Scored: {b.total_scored_entities}</div>
                    <div>Investigated: {b.investigated_entities}</div>
                    <div>Confirmed Fraud: <strong className="text-rose-400">{b.confirmed_fraud_count}</strong></div>
                    <div>False Positives: {b.false_positive_count}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Threshold Suggestions */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-base font-bold text-white">Deterministic Threshold Adjustment Recommendations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {calibration.suggested_adjustments.map((adj) => (
                <div key={adj.suggestion_id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300 font-semibold">{adj.target_metric_or_detector}</span>
                    <span className="text-emerald-400 font-semibold">-{adj.expected_fpr_reduction_pct}% FPR</span>
                  </div>
                  <p className="text-xs text-slate-400">{adj.rationale}</p>
                  <div className="flex items-center gap-4 text-xs pt-2 text-slate-300">
                    <div>Current: <strong className="text-rose-400">{adj.current_threshold}</strong></div>
                    <div>→ Suggested: <strong className="text-emerald-400">{adj.suggested_threshold}</strong></div>
                    <div>Retention: <strong className="text-sky-400">{adj.expected_true_positive_retention_pct}%</strong></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Detector Versions */}
      {activeTab === 'versions' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Version ID</th>
                <th className="p-3">Detector</th>
                <th className="p-3">Version</th>
                <th className="p-3">Status</th>
                <th className="p-3">Change Rationale</th>
                <th className="p-3">Created By</th>
                <th className="p-3">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {versions.map((ver) => (
                <tr key={ver.version_id} className="hover:bg-slate-800/50">
                  <td className="p-3 font-mono text-slate-400">{ver.version_id}</td>
                  <td className="p-3 font-semibold text-white">{ver.detector_id}</td>
                  <td className="p-3 font-mono text-emerald-400">{ver.version_number}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded font-semibold text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {ver.status}
                    </span>
                  </td>
                  <td className="p-3 max-w-xs truncate">{ver.change_rationale}</td>
                  <td className="p-3 text-slate-400">{ver.created_by}</td>
                  <td className="p-3 text-slate-500">{new Date(ver.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdaptiveIntelligencePage;
