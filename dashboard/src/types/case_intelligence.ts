import { RiskLevel } from './index';
import { CasePriority, CaseStatus } from './cases';

export type CaseCorrelationSignal =
  | 'SHARED_ACCOUNT'
  | 'SHARED_COUNTERPARTY'
  | 'SHARED_NETWORK'
  | 'SHARED_DETECTOR'
  | 'BEHAVIORAL_SIMILARITY'
  | 'TEMPORAL_CLUSTERING'
  | 'FINANCIAL_FLOW';

export interface CaseCorrelation {
  correlation_id: string;
  case_a: string;
  case_b: string;
  signal_type: CaseCorrelationSignal;
  signal_strength: number;
  confidence: number;
  explanation: string;
  common_entities: string[];
  common_detectors: string[];
  created_at: string;
}

export type CaseRelationshipNodeType =
  | 'CASE'
  | 'ALERT'
  | 'ACCOUNT'
  | 'TRANSACTION'
  | 'NETWORK'
  | 'EVIDENCE'
  | 'DECISION';

export type CaseRelationshipEdgeType =
  | 'LINKS_TO'
  | 'CORRELATED_WITH'
  | 'MEMBER_OF'
  | 'TRIGGERS'
  | 'SUPPORTS'
  | 'CONTRADICTS'
  | 'DERIVED_FROM'
  | 'RESOLVES';

export interface CaseRelationshipNode {
  id: string;
  label: string;
  type: CaseRelationshipNodeType;
  risk_score?: number;
  risk_level?: RiskLevel;
  status?: string;
  metadata?: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface CaseRelationshipEdge {
  id: string;
  source: string | any;
  target: string | any;
  type: CaseRelationshipEdgeType;
  strength: number;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface CaseRelationshipGraph {
  focal_case_id: string;
  nodes: CaseRelationshipNode[];
  edges: CaseRelationshipEdge[];
  total_nodes: number;
  total_edges: number;
  truncated: boolean;
}

export type CampaignStatus =
  | 'DISCOVERED'
  | 'UNDER_REVIEW'
  | 'CONFIRMED'
  | 'DISMISSED'
  | 'CLOSED';

export interface CampaignRiskFactor {
  factor_name: string;
  weight: number;
  raw_value: number;
  contribution: number;
  evidence: string;
}

export interface CampaignRiskExplanation {
  campaign_id: string;
  risk_score: number;
  confidence: number;
  factors: CampaignRiskFactor[];
  summary: string;
}

export interface Campaign {
  campaign_id: string;
  name: string;
  description: string;
  status: CampaignStatus;
  risk_score: number;
  confidence: number;
  case_ids: string[];
  account_ids: string[];
  network_ids: string[];
  alert_ids: string[];
  financial_exposure: number;
  confirmed_fraud_value: number;
  potential_exposure: number;
  primary_signals: CaseCorrelationSignal[];
  factor_contributions: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export type CollaboratorRole = 'OWNER' | 'COLLABORATOR' | 'WATCHER';

export interface CaseCollaborator {
  collaborator_id: string;
  case_id: string;
  user_id: string;
  username: string;
  role: CollaboratorRole;
  added_by: string;
  created_at: string;
}

export interface CaseComment {
  comment_id: string;
  case_id: string;
  author_id: string;
  author_name: string;
  content: string;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export type CaseActivityEventType =
  | 'CASE_CREATED'
  | 'CASE_ASSIGNED'
  | 'CASE_REASSIGNED'
  | 'CASE_STATUS_CHANGED'
  | 'EVIDENCE_ADDED'
  | 'EVIDENCE_UPDATED'
  | 'COMMENT_ADDED'
  | 'COMMENT_UPDATED'
  | 'COMMENT_DELETED'
  | 'COLLABORATOR_ADDED'
  | 'COLLABORATOR_REMOVED'
  | 'CAMPAIGN_LINKED'
  | 'CAMPAIGN_STATUS_CHANGED'
  | 'CASE_CORRELATED';

export interface CaseActivityEvent {
  event_id: string;
  case_id: string;
  actor_id: string;
  actor_name: string;
  event_type: CaseActivityEventType;
  summary: string;
  metadata: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

export type EvidenceRelationshipType =
  | 'SUPPORTS'
  | 'CONTRADICTS'
  | 'DERIVED_FROM'
  | 'RELATED_TO';

export interface EvidenceProvenance {
  provenance_id: string;
  evidence_id: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  relationship_type: EvidenceRelationshipType;
  derived_factor?: string;
  contribution: number;
  created_at: string;
}

export interface EnterpriseFraudPostureDriver {
  factor_name: string;
  impact: 'POSITIVE' | 'NEGATIVE';
  score_contribution: number;
  description: string;
}

export interface EnterpriseFraudPosture {
  posture_score: number;
  previous_score: number;
  score_delta: number;
  risk_level: RiskLevel;
  top_drivers: EnterpriseFraudPostureDriver[];
  positive_drivers: string[];
  negative_drivers: string[];
  summary: string;
  evaluated_at: string;
}

export interface CommandCenterSummary {
  active_investigations: number;
  critical_alerts: number;
  open_fraud_cases: number;
  confirmed_fraud_value: number;
  potential_exposure: number;
  active_campaigns_count: number;
  sla_breach_rate: number;
  high_risk_networks_count: number;
  top_campaigns: Campaign[];
  posture: EnterpriseFraudPosture;
}

export interface AddCollaboratorRequest {
  user_id: string;
  username: string;
  role: CollaboratorRole;
}

export interface AddCommentRequest {
  content: string;
}

export interface UpdateCommentRequest {
  content: string;
}

export interface CampaignUpdateRequest {
  status?: CampaignStatus;
  name?: string;
  description?: string;
}

export interface CaseCorrelationResponse {
  case_id: string;
  correlations_count: number;
  correlations: CaseCorrelation[];
}

export interface CaseEvidenceProvenanceResponse {
  case_id: string;
  provenance_count: number;
  records: EvidenceProvenance[];
}
