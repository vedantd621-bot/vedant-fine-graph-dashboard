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
  has_next: boolean;
  has_prev: boolean;
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
  is_frozen: boolean;
  frozen_at?: string;
}

export interface AccountTransactionItem {
  transaction_id: string;
  direction: 'INCOMING' | 'OUTGOING';
  counterparty: string;
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
