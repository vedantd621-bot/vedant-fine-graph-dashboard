import { Severity } from './alerts';
import { RiskLevel } from './accounts';

export type PriorityLevel = 'P0_CRITICAL' | 'P1_HIGH' | 'P2_MEDIUM' | 'P3_LOW';

export type TriageStatus =
  | 'NEW'
  | 'TRIAGED'
  | 'INVESTIGATING'
  | 'ESCALATED'
  | 'CONFIRMED_FRAUD'
  | 'FALSE_POSITIVE'
  | 'CLOSED';

export type SLAStatus = 'WITHIN_SLA' | 'AT_RISK' | 'BREACHED' | 'RESOLVED';

export interface PriorityFactor {
  factor_name: string;
  weight: number;
  raw_value: number;
  contribution: number;
  evidence: string;
}

export interface AlertPriorityExplanation {
  alert_id: string;
  priority_score: number;
  priority_level: PriorityLevel;
  factors: PriorityFactor[];
  summary: string;
}

export interface PrioritizedAlert {
  alert_id: string;
  detection_type: string;
  severity: Severity;
  confidence: number;
  primary_account: string;
  related_accounts: string[];
  risk_score?: number | null;
  risk_level?: RiskLevel | null;
  priority_score: number;
  priority_level: PriorityLevel;
  triage_status: TriageStatus;
  assigned_investigator?: string | null;
  created_at: string;
  updated_at?: string | null;
  sla_deadline: string;
  sla_status: SLAStatus;
  time_remaining_minutes: number;
  description: string;
  total_amount?: number | null;
  currency: string;
  duplicate_group_id?: string | null;
  correlation_group_id?: string | null;
  network_id?: string | null;
  case_id?: string | null;
}

export interface PrioritizedAlertListResponse {
  data: PrioritizedAlert[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
}

export interface AlertTriageRequest {
  new_status: TriageStatus;
  notes?: string;
  escalation_reason?: string;
}

export interface AlertAssignRequest {
  assigned_to: string;
  notes?: string;
}

export interface BulkAlertTriageRequest {
  alert_ids: string[];
  new_status: TriageStatus;
  notes?: string;
}

export interface BulkAlertAssignRequest {
  alert_ids: string[];
  assigned_to: string;
  notes?: string;
}

export interface BulkOperationResult {
  success_count: number;
  failed_count: number;
  processed_ids: string[];
  errors: Record<string, string>;
}

export interface InvestigatorWorkload {
  investigator_id: string;
  username: string;
  assigned_alerts: number;
  open_cases: number;
  critical_alerts: number;
  overdue_alerts: number;
  avg_resolution_hours: number;
  alerts_resolved: number;
  false_positive_rate: number;
  active_investigations: number;
}

export interface WorkloadListResponse {
  investigators: InvestigatorWorkload[];
  total_assigned_alerts: number;
  total_open_cases: number;
}

export interface SLAItem {
  alert_id: string;
  priority_level: PriorityLevel;
  triage_status: TriageStatus;
  created_at: string;
  sla_deadline: string;
  sla_status: SLAStatus;
  time_remaining_minutes: number;
  assigned_investigator?: string | null;
}

export interface SLASummary {
  total_tracked: number;
  within_sla_count: number;
  at_risk_count: number;
  breached_count: number;
  compliance_rate: number;
  items: SLAItem[];
}

export interface OperationsSummary {
  alerts_today: number;
  critical_alerts: number;
  confirmed_fraud: number;
  false_positives: number;
  open_investigations: number;
  sla_compliance_rate: number;
  avg_resolution_hours: number;
  total_fraud_value_prevented: number;
  currency: string;
  top_detectors: { detector: string; count: number }[];
  active_networks_count: number;
}

export interface FraudTrendPoint {
  timestamp: string;
  alert_count: number;
  critical_count: number;
  confirmed_fraud_count: number;
  false_positive_count: number;
  fraud_amount: number;
}

export interface FraudTrendsResponse {
  interval: string;
  points: FraudTrendPoint[];
  total_alerts: number;
  total_amount: number;
}

export interface DetectorPerformanceMetrics {
  detection_type: string;
  alert_count: number;
  confirmed_fraud_count: number;
  false_positive_count: number;
  operational_confirmation_rate: number;
  avg_risk_score: number;
  total_amount: number;
}

export interface DetectorPerformanceResponse {
  detectors: DetectorPerformanceMetrics[];
  disclaimer: string;
}

export interface SearchResultItem {
  entity_type: string;
  entity_id: string;
  title: string;
  subtitle?: string | null;
  severity_or_status?: string | null;
  risk_or_priority?: string | null;
  metadata: Record<string, any>;
}

export interface UnifiedSearchResponse {
  query: string;
  total_matches: number;
  results: SearchResultItem[];
}
