export type TenantStatus = 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'DISABLED';
export type ConfigVersionStatus = 'DRAFT' | 'ACTIVE' | 'RETIRED';
export type PolicyEffect = 'ALLOW' | 'DENY';

export interface TenantQuota {
  max_users: number;
  max_teams: number;
  max_cases_per_month: number;
  max_simulations_per_day: number;
  max_api_rps: number;
}

export interface TenantConfiguration {
  alert_priority_threshold: number;
  default_sla_hours: number;
  auto_assign_leads: boolean;
  notification_channels: string[];
  retention_days_audit: number;
  retention_days_cases: number;
  custom_risk_weights: Record<string, number>;
}

export interface ConfigurationVersion {
  version_id: string;
  tenant_id: string;
  config_type: string;
  version: number;
  configuration: TenantConfiguration;
  created_by: string;
  created_at: string;
  status: ConfigVersionStatus;
  release_notes?: string;
}

export interface Tenant {
  tenant_id: string;
  name: string;
  slug: string;
  status: TenantStatus;
  created_at: string;
  updated_at: string;
  quotas: TenantQuota;
  active_config_version?: string;
  metadata: Record<string, any>;
}

export interface Organization {
  org_id: string;
  tenant_id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
}

export interface BusinessUnit {
  unit_id: string;
  tenant_id: string;
  org_id: string;
  name: string;
  code: string;
  created_at: string;
}

export interface TeamMember {
  user_id: string;
  username: string;
  role: string;
  joined_at: string;
}

export interface InvestigationTeam {
  team_id: string;
  tenant_id: string;
  org_id: string;
  name: string;
  description: string;
  lead_user_id?: string;
  members: TeamMember[];
  created_at: string;
}

export interface TenantUsageMetrics {
  tenant_id: string;
  active_users: number;
  active_teams: number;
  cases_created_this_month: number;
  simulations_run_today: number;
  transactions_processed_total: number;
  alerts_generated_total: number;
  api_requests_total: number;
  storage_bytes_estimate: number;
}

export interface PolicyCondition {
  field: string;
  operator: string;
  value: any;
}

export interface Policy {
  policy_id: string;
  tenant_id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  conditions: PolicyCondition[];
  effect: PolicyEffect;
  priority: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyEvaluationRequest {
  user_id: string;
  username?: string;
  role: string;
  tenant_id: string;
  org_id?: string;
  team_ids?: string[];
  resource_type: string;
  resource_id: string;
  resource_tenant_id: string;
  action: string;
  environment?: Record<string, any>;
}

export interface PolicyEvaluationResult {
  effect: PolicyEffect;
  is_allowed: boolean;
  matched_policy_id?: string;
  reason: string;
  evaluated_at: string;
}

export interface ControlPlaneOverview {
  scope: string;
  total_tenants?: number;
  active_tenants?: number;
  total_users?: number;
  total_policies?: number;
  tenant_id: string;
  tenant_name?: string;
  status?: string;
  organization_count?: number;
  team_count?: number;
  user_count?: number;
  policy_count?: number;
  usage?: TenantUsageMetrics;
}
