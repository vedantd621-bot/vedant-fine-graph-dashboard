import { RiskLevel } from './index';

export type EvolutionTimeWindow = '5m' | '1h' | '6h' | '24h' | '7d' | '30d';

export type RiskTrajectory =
  | 'STABLE'
  | 'INCREASING'
  | 'RAPIDLY_INCREASING'
  | 'DECREASING'
  | 'VOLATILE';

export type ForecastHorizon = 'next_1h' | 'next_6h' | 'next_24h' | 'next_7d';

export type ForecastStatus = 'SUFFICIENT_DATA' | 'INSUFFICIENT_HISTORY';

export interface NetworkMetricsSnapshot {
  node_count: number;
  edge_count: number;
  transaction_count: number;
  financial_exposure: number;
  average_risk: number;
  network_risk: number;
  new_accounts_count: number;
  new_counterparties_count: number;
  captured_at: string;
}

export interface NetworkVelocity {
  tx_velocity_per_hour: number;
  account_velocity_per_hour: number;
  counterparty_velocity_per_hour: number;
  exposure_velocity_per_hour: number;
  risk_growth_per_hour: number;
}

export interface NetworkEvolutionSnapshot {
  network_id: string;
  window: EvolutionTimeWindow;
  previous_snapshot?: NetworkMetricsSnapshot;
  current_snapshot: NetworkMetricsSnapshot;
  growth_rate: number;
  risk_delta: number;
  exposure_delta: number;
  velocity: NetworkVelocity;
  trajectory: RiskTrajectory;
  new_entities: string[];
  removed_entities: string[];
  emerging_patterns: string[];
  generated_at: string;
}

export interface EmergingNetwork {
  network_id: string;
  name: string;
  emergence_score: number;
  confidence: number;
  risk_level: RiskLevel;
  growth_metrics: Record<string, number>;
  supporting_signals: string[];
  explanation: string;
  first_seen: string;
  last_seen: string;
}

export interface HorizonForecast {
  horizon: ForecastHorizon;
  forecast_score?: number;
  confidence: number;
  trend: string;
  drivers: string[];
  status: ForecastStatus;
}

export interface NetworkRiskForecast {
  network_id: string;
  current_risk: number;
  horizons: Record<string, HorizonForecast>;
  overall_trend: RiskTrajectory;
  status: ForecastStatus;
  evaluated_at: string;
}

export type EntityType = 'account' | 'device' | 'ip' | 'counterparty' | 'network';

export interface EntityRiskTrajectory {
  entity_type: EntityType;
  entity_id: string;
  current_risk: number;
  previous_risk: number;
  risk_delta: number;
  risk_velocity: number;
  trajectory: RiskTrajectory;
  top_drivers: string[];
  updated_at: string;
}

export type EarlyWarningSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type EarlyWarningStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'ESCALATED' | 'DISMISSED';

export type WarningActionRecommendation =
  | 'REVIEW_NETWORK'
  | 'REVIEW_ACCOUNT'
  | 'ESCALATE_CASE'
  | 'MONITOR_ACTIVITY'
  | 'INVESTIGATE_COUNTERPARTIES'
  | 'REVIEW_TRANSACTION_FLOW';

export interface EarlyWarning {
  warning_id: string;
  severity: EarlyWarningSeverity;
  status: EarlyWarningStatus;
  entity_type: string;
  entity_id: string;
  risk_score: number;
  confidence: number;
  trigger_signals: string[];
  explanation: string;
  recommended_action: WarningActionRecommendation;
  audit_notes?: string;
  acknowledged_by?: string;
  created_at: string;
  updated_at: string;
}

export interface EarlyWarningActionRequest {
  notes?: string;
}

export type EnterpriseThreatLevel = 'NORMAL' | 'ELEVATED' | 'HIGH' | 'SEVERE' | 'CRITICAL';

export interface EnterpriseThreatAssessment {
  threat_level: EnterpriseThreatLevel;
  score: number;
  previous_level: EnterpriseThreatLevel;
  score_delta: number;
  drivers: string[];
  evaluated_at: string;
}

export interface EnterpriseRiskForecast {
  current_threat_score: number;
  threat_level: EnterpriseThreatLevel;
  forecast_1h: number;
  forecast_6h: number;
  forecast_24h: number;
  forecast_7d: number;
  confidence: number;
  data_sufficiency: string;
  top_drivers: string[];
  evaluated_at: string;
}

export type PatternType =
  | 'CIRCULAR_LOOP'
  | 'RAPID_DISPERSION'
  | 'MULTI_INFLOW_FUNNEL'
  | 'BURST_ACTIVITY'
  | 'LAYERED_CHAIN';

export interface DiscoveredPattern {
  pattern_id: string;
  name: string;
  pattern_type: PatternType;
  frequency: number;
  confidence: number;
  risk_score: number;
  affected_entities: string[];
  financial_exposure: number;
  explanation: string;
  supporting_signals: string[];
  related_cases: string[];
  related_campaigns: string[];
  related_networks: string[];
  created_at: string;
}

export interface PatternSimilarityResponse {
  pattern_a: string;
  pattern_b: string;
  similarity_score: number;
  shared_signals: string[];
  shared_entities: string[];
  explanation: string;
}
