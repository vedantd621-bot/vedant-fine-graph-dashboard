export * from './orchestration';
export * from './autonomous_intelligence';
export * from './advanced_intelligence';
export * from './case_intelligence';
export * from './networks';
export * from './behavior';
export * from './features';
export * from './cases';
export * from './auth';
export * from './realtime';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';
export type DetectionType =
  | 'FUNNEL'
  | 'ONE_TO_MANY'
  | 'CHAIN'
  | 'CIRCULAR_FLOW'
  | 'LAYERED_NETWORK'
  | 'HIGH_DEGREE'
  | 'MONEY_TRAIL';

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface AlertSummary {
  alert_id: string;
  detection_type: DetectionType;
  severity: AlertSeverity;
  confidence: number;
  primary_account: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  created_at: string;
  status: AlertStatus;
  description: string;
  total_amount?: number;
  currency: string;
}

export interface DetectionEvidence {
  reason_summary: string;
  metric_name: string;
  metric_value: any;
  threshold_value: any;
  source_accounts?: string[];
  destination_accounts?: string[];
  intermediary_accounts?: string[];
  path_nodes?: string[];
  cycle_length?: number;
  hop_count?: number;
  inflow_amount?: number;
  outflow_amount?: number;
}

export interface AlertDetail {
  alert_id: string;
  detection_type: DetectionType;
  severity: AlertSeverity;
  confidence: number;
  primary_account: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  created_at: string;
  updated_at?: string;
  status: AlertStatus;
  description: string;
  evidence: DetectionEvidence;
  related_accounts: string[];
  transaction_ids: string[];
  total_amount?: number;
  currency: string;
  reasons: string[];
}

export interface GraphFeatures {
  account_id: string;
  pagerank: number;
  wcc_id?: number;
  louvain_community_id?: number;
  in_degree: number;
  out_degree: number;
  total_degree: number;
  community_size: number;
  total_volume: number;
}

export interface RuleSignals {
  account_id: string;
  funnel_flag: boolean;
  circular_flag: boolean;
  layered_flag: boolean;
  one_to_many_flag: boolean;
  chain_flag: boolean;
  high_degree_flag: boolean;
  active_detections_count: number;
  raw_rule_score: number;
  detection_types: string[];
}

export interface CounterpartyInfo {
  counterparty: string;
  direction: 'INCOMING' | 'OUTGOING';
  transaction_id: string;
  amount: number;
  currency: string;
  timestamp: string;
  scenario_id?: string;
}

export interface AccountSummary {
  account_id: string;
  account_type: string;
  bank_id?: string;
  bank_name?: string;
  owner_id?: string;
  owner_name?: string;
  risk_score: number;
  risk_level: RiskLevel;
  total_degree: number;
  in_degree: number;
  out_degree: number;
  pagerank: number;
  louvain_community_id?: number;
  wcc_id?: number;
  total_volume: number;
  is_frozen: boolean;
  updated_at?: string;
}

export interface AccountDetail {
  account_id: string;
  account_type: string;
  bank_id?: string;
  bank_name?: string;
  owner_id?: string;
  owner_name?: string;
  risk_score: number;
  risk_level: RiskLevel;
  model_version: string;
  calculated_at?: string;
  features: GraphFeatures;
  rule_signals: RuleSignals;
  risk_reasons: string[];
  counterparties?: CounterpartyInfo[];
  in_degree?: number;
  out_degree?: number;
  total_degree?: number;
  pagerank?: number;
  community_id?: number;
  wcc_id?: number;
  is_frozen: boolean;
  frozen_at?: string;
}

export interface AccountTransactionItem {
  transaction_id: string;
  direction: 'INCOMING' | 'OUTGOING';
  counterparty: string;
  counterparty_account?: string;
  counterparty_name?: string;
  amount: number;
  currency: string;
  timestamp: string;
  transaction_type: string;
  scenario_id?: string;
  channel?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'Account' | 'Person' | 'Bank';
  risk_score?: number;
  risk_level?: RiskLevel;
  is_frozen?: boolean;
  metadata?: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  id: string;
  source: string | any;
  target: string | any;
  type: 'TRANSFERRED_TO' | 'OWNS' | 'HOSTED_BY';
  amount?: number;
  currency?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface GraphPayload {
  focal_account_id?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  is_truncated: boolean;
  total_nodes: number;
  total_edges: number;
}

export interface DashboardSummary {
  total_accounts: number;
  total_transactions: number;
  open_alerts: number;
  investigating_alerts: number;
  resolved_alerts: number;
  high_risk_accounts: number;
  critical_risk_accounts: number;
  total_transaction_volume: number;
  currency: string;
  updated_at: string;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
  total: number;
  total_accounts?: number;
}

export interface AlertTrendPoint {
  timestamp: string;
  count: number;
  severity_breakdown: Record<string, number>;
}

export interface MoneyTrailStep {
  from_account: string;
  to_account: string;
  transaction_id: string;
  amount: number;
  currency: string;
  timestamp: string;
  scenario_id?: string;
}

export interface MoneyTrailPath {
  path_id: string;
  origin: string;
  destination: string;
  hop_count: number;
  total_amount: number;
  path_nodes: string[];
  steps: MoneyTrailStep[];
}

export interface SearchResults {
  query: string;
  accounts: AccountSummary[];
  alerts: AlertSummary[];
  transaction_ids: string[];
}

// ---------------------------------------------------------------------------
// Phase 11 Advanced Intelligence & Timeline Types
// ---------------------------------------------------------------------------

export type TimelineEventType =
  | 'TRANSACTION'
  | 'DETECTOR_MATCH'
  | 'RISK_SCORE_CHANGE'
  | 'ALERT_CREATED'
  | 'STATUS_CHANGED'
  | 'ACCOUNT_FROZEN'
  | 'CASE_CREATED'
  | 'CASE_UPDATED'
  | 'INVESTIGATION_NOTE'
  | 'EVIDENCE_ATTACHED';

export interface ExplainableRiskFactor {
  factor_type: string;
  description: string;
  severity: AlertSeverity;
  weight: number;
  evidence_reference?: string;
  value?: any;
}

export interface RiskExplanationResponse {
  entity_id: string;
  entity_type: string;
  risk_score: number;
  risk_level: RiskLevel;
  reasons: ExplainableRiskFactor[];
  summary: string;
}

export interface EntityRiskProfile {
  entity_id: string;
  entity_type: string;
  name?: string;
  risk_score: number;
  risk_level: RiskLevel;
  major_risk_factors: ExplainableRiskFactor[];
  detector_hits: string[];
  graph_metrics: Record<string, any>;
  connected_suspicious_entities: Array<Record<string, any>>;
  recent_suspicious_activity: Array<Record<string, any>>;
  investigation_history: Array<Record<string, any>>;
  is_frozen: boolean;
  updated_at: string;
}

export interface InvestigationTimelineEvent {
  event_id: string;
  timestamp: string;
  event_type: TimelineEventType;
  actor?: string;
  entity_id: string;
  entity_type: string;
  title: string;
  description: string;
  evidence_ref?: string;
  metadata?: Record<string, any>;
}

export interface InvestigationTimelineResponse {
  entity_id: string;
  total_events: number;
  events: InvestigationTimelineEvent[];
}

export interface AlertCorrelation {
  alert_id: string;
  related_alerts_count: number;
  correlated_alerts: AlertSummary[];
  common_entities: string[];
  common_detectors: string[];
  correlation_strength: number;
  correlation_reason: string;
}

export interface AlertRecommendationItem {
  action_type: string;
  title: string;
  description: string;
  priority: AlertSeverity;
  target_entity?: string;
  evidence_summary: string;
}

export interface AlertRecommendationsResponse {
  alert_id: string;
  recommendations: AlertRecommendationItem[];
}

export interface InvestigationAnalytics {
  cases_by_status: Record<string, number>;
  cases_by_priority: Record<string, number>;
  alerts_by_detector: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  high_risk_entities_count: number;
  active_investigators_count: number;
  top_suspicious_communities: Array<Record<string, any>>;
}

export * from './operations';
export * from './notifications';

export * from './tenancy';

export * from './orchestration';
export * from './advanced_intelligence';
export * from './autonomous_intelligence';
export * from './behavior';
export * from './cases';
export * from './case_intelligence';
export * from './enterprise';
export * from './features';
export * from './networks';
export * from './realtime';
export * from './auth';
