/**
 * FinGraph Autonomous Fraud Intelligence, Shadow Detection, Risk Calibration & Threat Propagation Types.
 */

export type RecommendationStatus = 'PROPOSED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'DEPLOYED';
export type RecommendationType = 'THRESHOLD_TUNE' | 'NEW_RULE' | 'RULE_SUPPRESSION' | 'WEIGHT_ADJUSTMENT' | 'FEATURE_ENHANCEMENT';
export type EmergingPatternType = 'STRUCTURAL_CYCLE' | 'VELOCITY_BURST' | 'CENTRALITY_SPIKE' | 'DENSE_COMMUNITY' | 'CROSS_CAMPAIGN' | 'UNTRACKED_PROXY_HOP';
export type GapPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type VersionStatus = 'ACTIVE' | 'SHADOW' | 'DEPRECATED' | 'ARCHIVED';
export type GroundTruthStatus = 'SUFFICIENT_GROUND_TRUTH' | 'INSUFFICIENT_GROUND_TRUTH';

export interface DetectionGap {
  gap_id: string;
  pattern_type: EmergingPatternType;
  title: string;
  description: string;
  uncovered_motif_count: number;
  affected_entities: string[];
  estimated_financial_exposure: number;
  priority: GapPriority;
  sample_motifs: Array<Record<string, any>>;
  status: string;
  discovered_at: string;
}

export interface StatusHistoryEntry {
  from_status: string;
  to_status: string;
  transitioned_by: string;
  transitioned_at: string;
  reason?: string;
}

export interface DetectorRecommendation {
  recommendation_id: string;
  recommendation_type: RecommendationType;
  title: string;
  description: string;
  target_detector_id?: string;
  gap_id?: string;
  suggested_parameters: Record<string, any>;
  expected_impact_summary: string;
  confidence_score: number;
  status: RecommendationStatus;
  created_by: string;
  reviewed_by?: string;
  created_at: string;
  reviewed_at?: string;
  deployed_at?: string;
  status_history: StatusHistoryEntry[];
  evidence_notes?: string;
}

export interface DetectorVersion {
  version_id: string;
  detector_id: string;
  version_number: string;
  parameters: Record<string, any>;
  status: VersionStatus;
  created_by: string;
  change_rationale: string;
  recommendation_id?: string;
  created_at: string;
}

export interface RecommendationReviewRequest {
  status: RecommendationStatus;
  notes?: string;
  override_parameters?: Record<string, any>;
}

export interface AutonomousIntelligenceSummary {
  active_gaps_count: number;
  pending_recommendations_count: number;
  approved_recommendations_count: number;
  active_detector_versions_count: number;
  highest_priority_gap?: DetectionGap;
  recent_recommendations: DetectorRecommendation[];
  generated_at: string;
}

export interface ShadowSimulationRequest {
  detector_id: string;
  recommendation_id?: string;
  parameters?: Record<string, any>;
  time_window_hours?: number;
  sample_size_limit?: number;
}

export interface ShadowSimulationResult {
  simulation_id: string;
  detector_id: string;
  recommendation_id?: string;
  time_window_hours: number;
  transactions_evaluated_count: number;
  alerts_would_fire_count: number;
  overlap_with_prod_alerts_count: number;
  novel_detections_count: number;
  estimated_precision?: number;
  estimated_recall?: number;
  estimated_fpr: number;
  ground_truth_status: GroundTruthStatus;
  coverage_percentage: number;
  findings_summary: string;
  executed_at: string;
  execution_time_ms: number;
  evaluated_parameters: Record<string, any>;
}

export interface ScoreBucket {
  bucket_id: string;
  range_min: number;
  range_max: number;
  total_scored_entities: number;
  investigated_entities: number;
  confirmed_fraud_count: number;
  false_positive_count: number;
  confirmation_rate: number;
  false_positive_rate: number;
}

export interface ThresholdAdjustmentSuggestion {
  suggestion_id: string;
  target_metric_or_detector: string;
  current_threshold: number;
  suggested_threshold: number;
  expected_fpr_reduction_pct: number;
  expected_true_positive_retention_pct: number;
  rationale: string;
}

export interface RiskCalibrationReport {
  report_id: string;
  evaluation_window_days: number;
  buckets: ScoreBucket[];
  overall_confirmation_rate: number;
  drift_detected: boolean;
  drift_magnitude: number;
  suggested_adjustments: ThresholdAdjustmentSuggestion[];
  calibration_notes: string;
  generated_at: string;
}

export interface PropagationStep {
  step_index: number;
  step_time_offset_sec: number;
  mechanism: string;
  reached_entities: string[];
  new_exposure_amount: number;
  step_risk_delta: number;
  description: string;
}

export interface PropagatedEntity {
  entity_id: string;
  entity_type: string;
  distance_from_origin: number;
  risk_score: number;
  exposure_amount: number;
  infection_probability: number;
  propagation_path: string[];
}

export interface PropagationTopologyNode {
  id: string;
  label: string;
  risk: number;
  hop: number;
  exposure: number;
  type?: string;
}

export interface PropagationTopologyEdge {
  source: string;
  target: string;
  amount: number;
  mechanism: string;
  step: number;
}

export interface PropagationTopology {
  nodes: PropagationTopologyNode[];
  edges: PropagationTopologyEdge[];
}

export interface ThreatPropagationAnalysis {
  analysis_id: string;
  origin_entity_id: string;
  max_hops: number;
  time_window_hours: number;
  propagation_score: number;
  risk_velocity: number;
  total_affected_entities: number;
  total_financial_exposure: number;
  steps: PropagationStep[];
  affected_entities_details: PropagatedEntity[];
  topology: PropagationTopology;
  containment_recommendations: string[];
  analyzed_at: string;
}
