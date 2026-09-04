import { RiskLevel } from './index';

export type TemporalWindow = '5m' | '1h' | '24h' | '7d' | '30d';

export type AnomalyType =
  | 'VOLUME_SPIKE'
  | 'VELOCITY_BURST'
  | 'COUNTERPARTY_BURST'
  | 'UNUSUAL_OUTGOING_RATIO'
  | 'HIGH_VALUE_DEVIATION'
  | 'NEW_TOPOLOGY_CONNECTION';

export interface EntityBehaviorBaseline {
  entity_id: string;
  historical_transaction_count: number;
  historical_volume: number;
  avg_transaction_amount: number;
  std_dev_amount: number;
  max_transaction_amount: number;
  avg_velocity_per_hour: number;
  incoming_volume_ratio: number;
  outgoing_volume_ratio: number;
  unique_counterparties_count: number;
  common_counterparties: string[];
  baseline_window_days: number;
  last_computed_at: string;
}

export interface BehavioralAnomaly {
  anomaly_id: string;
  anomaly_type: AnomalyType;
  severity: string;
  anomaly_score: number;
  window: TemporalWindow;
  metric_name: string;
  observed_value: number;
  baseline_value: number;
  deviation_ratio: number;
  description: string;
  evidence_reference?: string;
  detected_at: string;
}

export interface EntityBehaviorResponse {
  entity_id: string;
  baseline: EntityBehaviorBaseline;
  recent_transaction_count: number;
  recent_volume: number;
  active_window: TemporalWindow;
  anomalies: BehavioralAnomaly[];
  anomaly_score: number;
  is_anomalous: boolean;
  summary: string;
}

export interface EntitySimilarityItem {
  target_entity_id: string;
  similarity_score: number;
  shared_counterparties: string[];
  shared_communities: number[];
  shared_detectors: string[];
  volume_similarity: number;
  explanation: string;
}

export interface EntitySimilarityResponse {
  entity_id: string;
  similar_entities: EntitySimilarityItem[];
  total_matches: number;
}
