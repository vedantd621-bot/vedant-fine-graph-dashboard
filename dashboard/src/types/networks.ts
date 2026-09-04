import { RiskLevel } from './index';

export type NetworkType =
  | 'CIRCULAR_RING'
  | 'FAN_IN_CONSOLIDATION'
  | 'FAN_OUT_DISPERSION'
  | 'LAYERED_CHAIN'
  | 'COMMUNITY_SYNDICATE'
  | 'SHARED_INFRASTRUCTURE';

export type NetworkMemberRole =
  | 'ORIGINATOR'
  | 'AGGREGATOR'
  | 'DISPERSER'
  | 'MULE'
  | 'INTERMEDIARY'
  | 'MEMBER';

export interface FraudNetworkMember {
  account_id: string;
  role: NetworkMemberRole;
  pagerank: number;
  degree: number;
  risk_score: number;
  risk_level: RiskLevel;
  louvain_community_id?: number;
  inflow_amount?: number;
  outflow_amount?: number;
}

export interface NetworkRiskFactor {
  factor_name: string;
  factor_weight: number;
  raw_value: number;
  weighted_score: number;
  description: string;
  evidence_hint?: string;
}

export interface NetworkEvidence {
  evidence_id: string;
  network_id: string;
  evidence_type: string;
  title: string;
  description: string;
  source_entities: string[];
  target_entities: string[];
  amount?: number;
  confidence: number;
  created_at: string;
}

export interface NetworkTimelineEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  involved_accounts: string[];
  amount?: number;
  severity: string;
}

export interface FraudNetwork {
  network_id: string;
  name: string;
  network_type: NetworkType;
  risk_score: number;
  risk_level: RiskLevel;
  total_members: number;
  total_volume: number;
  hub_account_id?: string;
  community_id?: number;
  members: FraudNetworkMember[];
  risk_factors: NetworkRiskFactor[];
  evidence_items: NetworkEvidence[];
  timeline: NetworkTimelineEvent[];
  linked_case_ids: string[];
  discovered_at: string;
  last_updated_at: string;
}

export interface NetworkSummary {
  network_id: string;
  name: string;
  network_type: NetworkType;
  risk_score: number;
  risk_level: RiskLevel;
  total_members: number;
  total_volume: number;
  hub_account_id?: string;
  community_id?: number;
  linked_case_ids: string[];
  discovered_at: string;
}

export interface NetworkListResponse {
  data: NetworkSummary[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next?: boolean;
    has_prev?: boolean;
  };
}

export interface NetworkDetail extends FraudNetwork {}

export interface NetworkMemberResponse {
  network_id: string;
  members: FraudNetworkMember[];
  total_members: number;
}

export interface NetworkEvidenceResponse {
  network_id: string;
  evidence: NetworkEvidence[];
  timeline: NetworkTimelineEvent[];
  total_evidence: number;
}

export interface NetworkRiskExplanationResponse {
  network_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  risk_factors: NetworkRiskFactor[];
  narrative_explanation: string;
}

export interface NetworkCreateCaseRequest {
  title?: string;
  priority?: string;
  description?: string;
}
