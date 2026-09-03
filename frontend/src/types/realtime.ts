import { AlertSeverity, AlertStatus, DetectionType, RiskLevel } from './index';

export type RealtimeEventType =
  | 'alert.created'
  | 'alert.updated'
  | 'risk.updated'
  | 'transaction.created'
  | 'graph.updated'
  | 'system.ping'
  | 'system.pong'
  | 'error';

export type ConnectionStatus = 'LIVE' | 'CONNECTING' | 'DISCONNECTED';

export interface RealtimeEvent<T = any> {
  event: RealtimeEventType;
  event_id: string;
  timestamp: string;
  version: number;
  data: T;
}

export interface AlertCreatedData {
  alert_id: string;
  detection_type: DetectionType;
  severity: AlertSeverity;
  confidence: number;
  primary_account: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  status: AlertStatus;
  description: string;
  total_amount?: number;
  currency: string;
  related_accounts?: string[];
}

export interface AlertUpdatedData {
  alert_id: string;
  previous_status?: AlertStatus;
  status: AlertStatus;
  updated_at: string;
  notes?: string;
}

export interface RiskUpdatedData {
  account_id: string;
  previous_score?: number;
  score: number;
  previous_level?: RiskLevel;
  risk_level: RiskLevel;
  model_version: string;
  reasons: string[];
  calculated_at: string;
}

export interface TransactionCreatedData {
  transaction_id: string;
  source_account: string;
  destination_account: string;
  amount: number;
  currency: string;
  timestamp: string;
  scenario_id?: string;
  channel?: string;
}

export interface GraphUpdatedData {
  account_id: string;
  change_type: string;
  related_account_id?: string;
  timestamp: string;
}
