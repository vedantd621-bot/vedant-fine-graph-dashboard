// FinGraph Master Enterprise Domain Types

export type DecisionVerdict = 'ALLOW' | 'REVIEW' | 'ESCALATE' | 'BLOCK' | 'CONFIRM_FRAUD' | 'FALSE_POSITIVE';
export type DecisionConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FraudDecision {
  decision_id: string;
  alert_id?: string;
  case_id?: string;
  entity_id?: string;
  tenant_id: string;
  verdict: DecisionVerdict;
  confidence: DecisionConfidence;
  risk_score: number;
  contributing_signals: string[];
  evidence_summary: string;
  recommendation: string;
  policy_version?: string;
  detector_versions: string[];
  created_by: string;
  created_at: string;
  is_override: boolean;
  override_reference?: string;
}

export interface DecisionOverride {
  override_id: string;
  decision_id: string;
  tenant_id: string;
  original_verdict: DecisionVerdict;
  override_verdict: DecisionVerdict;
  actor: string;
  reason: string;
  evidence_references: string[];
  policy_context?: string;
  created_at: string;
}

export interface SimulationParameter {
  name: string;
  current_value: any;
  hypothetical_value: any;
  description?: string;
}

export interface SimulationRequest {
  scenario_name: string;
  description?: string;
  parameters: SimulationParameter[];
  alert_ids?: string[];
  case_ids?: string[];
}

export interface SimulationResult {
  simulation_id: string;
  scenario_name: string;
  description: string;
  parameters: SimulationParameter[];
  predicted_alerts_changed: number;
  predicted_risk_change: number;
  predicted_cases_impacted: number;
  predicted_exposure_change: number;
  recommendation_changes: string[];
  simulation_notes: string;
  is_production_safe: boolean;
  executed_at: string;
  executed_by: string;
}

export interface FraudKPIs {
  tenant_id: string;
  fraud_rate: number;
  fraud_count: number;
  confirmed_fraud: number;
  false_positives: number;
  blocked_transactions: number;
  escalations: number;
  alert_volume: number;
  open_alerts: number;
  calculated_at: string;
  data_quality_note: string;
}

export interface FinancialKPIs {
  tenant_id: string;
  suspicious_volume: number;
  confirmed_fraud_exposure: number;
  prevented_loss: number;
  estimated_loss: number;
  recovered_amount: number;
  average_case_exposure: number;
  calculated_at: string;
  data_quality_note: string;
}

export interface OperationsKPIs {
  tenant_id: string;
  open_cases: number;
  investigation_backlog: number;
  avg_investigation_hours: number;
  median_investigation_hours: number;
  sla_compliance_rate: number;
  investigator_workload: Record<string, number>;
  queue_depth: number;
  calculated_at: string;
  data_quality_note: string;
}

export interface DetectionKPIs {
  tenant_id: string;
  detector_hit_rate: number;
  precision_proxy: number;
  false_positive_rate: number;
  detector_contribution: Record<string, number>;
  detector_drift: Record<string, number>;
  detector_volume: number;
  calculated_at: string;
  data_quality_note: string;
}

export interface NetworkKPIs {
  tenant_id: string;
  active_fraud_networks: number;
  emerging_networks: number;
  high_risk_hubs: number;
  campaign_count: number;
  network_exposure: number;
  calculated_at: string;
  data_quality_note: string;
}

export interface ExecutiveFraudPosture {
  tenant_id: string;
  posture_score: number;
  threat_level: string;
  fraud_trend: string;
  financial_exposure: number;
  operational_backlog: number;
  detector_health: number;
  emerging_networks: number;
  campaign_risk: number;
  early_warnings: number;
  positive_drivers: string[];
  negative_drivers: string[];
  executive_summary: string;
  calculated_at: string;
}

export interface ExecutiveInsight {
  insight_id: string;
  tenant_id: string;
  title: string;
  description: string;
  evidence: string[];
  severity: string;
  metric_name?: string;
  metric_value?: number;
  generated_at: string;
}

export interface KPIAnomaly {
  anomaly_id: string;
  tenant_id: string;
  metric: string;
  baseline: number;
  current: number;
  deviation: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  explanation: string;
  detected_at: string;
}

export interface FraudTrendPoint {
  timestamp: string;
  fraud_count: number;
  alert_volume: number;
  risk_average: number;
  exposure: number;
  window: string;
  sample_size: number;
  completeness: number;
  confidence: number;
}

export interface EnterpriseKPIBundle {
  tenant_id: string;
  fraud: FraudKPIs;
  financial: FinancialKPIs;
  operations: OperationsKPIs;
  detection: DetectionKPIs;
  network: NetworkKPIs;
  posture: ExecutiveFraudPosture;
  insights: ExecutiveInsight[];
  anomalies: KPIAnomaly[];
  calculated_at: string;
}

export type ReportType =
  | 'EXECUTIVE_FRAUD_REPORT'
  | 'FRAUD_NETWORK_REPORT'
  | 'CAMPAIGN_REPORT'
  | 'INVESTIGATION_REPORT'
  | 'DETECTOR_PERFORMANCE_REPORT'
  | 'OPERATIONS_REPORT'
  | 'RISK_REPORT'
  | 'TENANT_POSTURE_REPORT';

export type ReportFormat = 'JSON' | 'CSV';
export type ReportStatus = 'PENDING' | 'GENERATING' | 'COMPLETED' | 'FAILED';
export type ScheduleFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY';

export interface ReportSnapshot {
  report_id: string;
  report_type: ReportType;
  tenant_id: string;
  title: string;
  format: ReportFormat;
  status: ReportStatus;
  created_by: string;
  created_at: string;
  parameters: Record<string, any>;
  data_version: string;
  analytics_version: string;
  policy_version?: string;
  content_hash?: string;
  row_count: number;
  content?: any;
}

export interface ReportSchedule {
  schedule_id: string;
  report_type: ReportType;
  tenant_id: string;
  frequency: ScheduleFrequency;
  title: string;
  format: ReportFormat;
  is_active: boolean;
  created_by: string;
  created_at: string;
  next_run_at?: string;
}
