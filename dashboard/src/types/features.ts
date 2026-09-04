export interface FeatureDefinition {
  name: string;
  data_type: string;
  description: string;
  source_module: string;
}

export interface EntityFeatureVector {
  account_id: string;
  extracted_at: string;
  transaction_count_1h: number;
  transaction_count_24h: number;
  transaction_volume_24h: number;
  avg_transaction_amount: number;
  max_transaction_amount: number;
  unique_counterparties: number;
  incoming_ratio: number;
  outgoing_ratio: number;
  pagerank: number;
  total_degree: number;
  in_degree: number;
  out_degree: number;
  community_size: number;
  detector_hit_count: number;
  high_risk_neighbor_count: number;
  alert_count: number;
  is_frozen: number;
  risk_score: number;
}

export interface FeatureStoreExportRequest {
  account_ids?: string[];
  format?: 'csv' | 'json';
  min_risk_score?: number;
}

export interface FeatureStoreExportResponse {
  format: string;
  total_entities: number;
  feature_count: number;
  extracted_at: string;
  features_json?: EntityFeatureVector[];
  features_csv?: string;
}
