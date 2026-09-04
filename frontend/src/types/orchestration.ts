/**
 * FinGraph Intelligence Orchestration & Investigation Automation Types.
 */

export type WorkflowState = 'CREATED' | 'TRIAGED' | 'INVESTIGATING' | 'EVIDENCE_REVIEW' | 'DECISION_PENDING' | 'DECIDED' | 'CLOSED';
export type PriorityBand = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type EvidenceStrength = 'STRONG' | 'MODERATE' | 'WEAK' | 'INCONCLUSIVE';
export type EvidenceCategory = 'TRANSACTION' | 'GRAPH' | 'BEHAVIOR' | 'NETWORK' | 'CAMPAIGN' | 'CASE_HISTORY' | 'DECISION_HISTORY' | 'THREAT_PROPAGATION';
export type TaskStatus = 'OPEN' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED';

export interface PriorityFactor {
  name: string;
  weight: number;
  raw_value: number;
  weighted_score: number;
  description: string;
}

export interface InvestigationPriorityScore {
  priority_score: number;
  priority_band: PriorityBand;
  factors: PriorityFactor[];
  explanation: string;
  calculated_at: string;
}

export interface RankedEvidenceItem {
  evidence_id: string;
  category: EvidenceCategory;
  title: string;
  description: string;
  strength: EvidenceStrength;
  confidence: number;
  source: string;
  timestamp: string;
  explanation: string;
  weight: number;
  raw_data?: Record<string, any>;
}

export interface CorrelationGroup {
  group_id: string;
  primary_alert_id: string;
  correlated_alert_ids: string[];
  correlation_score: number;
  reasons: string[];
  shared_signals: Record<string, any>;
  explanation: string;
  correlated_at: string;
}

export interface UnifiedTimelineEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  source: string;
  actor?: string;
  entity_refs: string[];
  severity?: string;
  metadata?: Record<string, any>;
}

export interface InvestigationTask {
  task_id: string;
  case_id: string;
  title: string;
  description: string;
  priority: PriorityBand;
  assignee: string;
  status: TaskStatus;
  created_by: string;
  created_at: string;
  due_at?: string;
  completed_at?: string;
  evidence_refs: string[];
  audit_refs: string[];
}

export interface CaseChecklistItem {
  item_id: string;
  case_id: string;
  title: string;
  is_completed: boolean;
  completed_by?: string;
  completed_at?: string;
  order: number;
}

export interface RelatedCase {
  case_id: string;
  relationship_score: number;
  relationship_reasons: string[];
  shared_entities: string[];
  status: string;
  created_at: string;
}

export interface InvestigationRecommendation {
  recommendation_id: string;
  case_id: string;
  title: string;
  reason: string;
  supporting_evidence: string[];
  confidence: number;
  priority: PriorityBand;
  action_type: string;
  is_actioned: boolean;
}

export interface InvestigationWorkflowTemplate {
  template_id: string;
  name: string;
  workflow_type: string;
  trigger_conditions: string[];
  required_checks: string[];
  recommended_evidence: string[];
  recommended_actions: string[];
  completion_conditions: string[];
}

export interface InvestigationBrief {
  brief_id: string;
  case_or_alert_id: string;
  title: string;
  executive_summary: string;
  risk_summary: string;
  financial_exposure: number;
  network_summary: string;
  behavior_summary: string;
  priority_assessment: InvestigationPriorityScore;
  related_alerts: string[];
  related_cases: RelatedCase[];
  campaign_associations: string[];
  ranked_evidence: RankedEvidenceItem[];
  unified_timeline: UnifiedTimelineEvent[];
  threat_propagation_summary: string;
  recommended_investigation_steps: InvestigationRecommendation[];
  open_questions: string[];
  generated_at: string;
}
