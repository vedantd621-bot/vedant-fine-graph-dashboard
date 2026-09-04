export type CaseStatus = 'OPEN' | 'IN_PROGRESS' | 'ESCALATED' | 'RESOLVED' | 'CLOSED';
export type CasePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type EvidenceType = 'TRANSACTION' | 'ACCOUNT' | 'GRAPH_PATH' | 'DETECTOR_RESULT' | 'NOTE' | 'RISK_FACTOR' | 'EXTERNAL';

export interface InvestigationNote {
  note_id: string;
  author_id: string;
  author_name: string;
  content: string;
  created_at: string;
}

export interface EvidenceItem {
  evidence_id: string;
  case_id?: string;
  type: EvidenceType;
  source: string;
  related_entity: string;
  title: string;
  description?: string;
  data: Record<string, any>;
  created_at: string;
  created_by: string;
  integrity_hash?: string;
}

export interface InvestigationCase {
  case_id: string;
  title: string;
  description: string;
  priority: CasePriority;
  status: CaseStatus;
  assigned_investigator?: string;
  linked_alerts: string[];
  linked_accounts: string[];
  linked_transactions: string[];
  notes: InvestigationNote[];
  evidence: EvidenceItem[];
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface InvestigationCaseSummary {
  case_id: string;
  title: string;
  priority: CasePriority;
  status: CaseStatus;
  assigned_investigator?: string;
  alerts_count: number;
  accounts_count: number;
  notes_count: number;
  evidence_count: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface CaseCreateRequest {
  title: string;
  description: string;
  priority?: CasePriority;
  assigned_investigator?: string;
  linked_alerts?: string[];
  linked_accounts?: string[];
  linked_transactions?: string[];
}

export interface CaseUpdateRequest {
  title?: string;
  description?: string;
  priority?: CasePriority;
  status?: CaseStatus;
}
