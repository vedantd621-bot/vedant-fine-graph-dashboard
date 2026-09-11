import { ControlPlaneOverview, Tenant, TenantQuota, TenantConfiguration, ConfigurationVersion, Organization, BusinessUnit, InvestigationTeam, TenantUsageMetrics, Policy, PolicyEffect, PolicyEvaluationRequest, PolicyEvaluationResult, TenantStatus } from '../types/tenancy';
﻿import axios from 'axios';
import {
  AccountDetail,
  FeatureStoreExportResponse,
  FeatureStoreExportRequest,
  EntityFeatureVector,
  FeatureDefinition,
  EntitySimilarityResponse,
  EntityBehaviorResponse,
  EntityBehaviorBaseline,
  NetworkCreateCaseRequest,
  NetworkSummary,
  NetworkRiskExplanationResponse,
  NetworkMemberResponse,
  NetworkListResponse,
  NetworkEvidenceResponse,
  NetworkDetail,
  AccountSummary,
  AccountTransactionItem,
  AlertCorrelation,
  AlertDetail,
  AlertRecommendationsResponse,
  AlertStatus,
  AlertSummary,
  ApiResponse,
  CaseCreateRequest,
  CaseListResponse,
  CaseUpdateRequest,
  DashboardSummary,
  EntityRiskProfile,
  EvidenceItem,
  GraphPayload,
  InvestigationAnalytics,
  InvestigationCase,
  InvestigationNote,
  InvestigationTimelineResponse,
  MoneyTrailPath,
  PaginatedResponse,
  RiskDistribution,
  RiskExplanationResponse,
  SearchResults,
} from '../types';

export const getApiBaseUrl = (): string => {
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && (window as any).__ENV__?.REACT_APP_API_BASE_URL) {
    return (window as any).__ENV__.REACT_APP_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    return `${protocol}//${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

export const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach dynamic baseURL and JWT token if stored
api.interceptors.request.use((config) => {
  if (!config.baseURL || config.baseURL === 'http://localhost:8000' || config.baseURL === 'http://127.0.0.1:8000') {
    config.baseURL = getApiBaseUrl();
  }
  const token = localStorage.getItem('fingraph_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 Unauthorized by clearing session
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const hadToken = !!localStorage.getItem('fingraph_token');
      localStorage.removeItem('fingraph_token');
      localStorage.removeItem('fingraph_user');
      if (hadToken && typeof window !== 'undefined' && !window.location.pathname.includes('login')) {
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export const apiClient = {
  // Health
  getHealth: async () => {
    const res = await api.get<{ status: string }>('/health');
    return res.data;
  },

  // Dashboard
  getDashboardSummary: async () => {
    const res = await api.get<ApiResponse<DashboardSummary>>('/api/v1/dashboard/summary');
    return res.data.data;
  },
  getRiskDistribution: async () => {
    const res = await api.get<ApiResponse<RiskDistribution>>('/api/v1/dashboard/risk-distribution');
    return res.data.data;
  },
  getTopRiskAccounts: async (limit: number = 10) => {
    const res = await api.get<ApiResponse<AccountSummary[]>>(
      `/api/v1/dashboard/top-risk-accounts?limit=${limit}`
    );
    return res.data.data;
  },

  // Alerts
  listAlerts: async (params?: {
    severity?: string;
    status?: string;
    detection_type?: string;
    page?: number;
    page_size?: number;
    sort?: string;
    order?: string;
  }) => {
    const res = await api.get<PaginatedResponse<AlertSummary>>('/api/v1/alerts', { params });
    return res.data;
  },
  getAlertDetail: async (alertId: string) => {
    const res = await api.get<ApiResponse<AlertDetail>>(`/api/v1/alerts/${alertId}`);
    return res.data.data;
  },
  updateAlertStatus: async (alertId: string, status: AlertStatus) => {
    const res = await api.patch<ApiResponse<AlertDetail>>(`/api/v1/alerts/${alertId}`, { status });
    return res.data.data;
  },
  getCorrelatedAlerts: async (alertId: string) => {
    const res = await api.get<AlertCorrelation>(`/api/v1/alerts/${alertId}/correlated`);
    return res.data;
  },
  getAlertRecommendations: async (alertId: string) => {
    const res = await api.get<AlertRecommendationsResponse>(`/api/v1/alerts/${alertId}/recommendations`);
    return res.data;
  },

  // Accounts
  listAccounts: async (params?: {
    risk_level?: string;
    search?: string;
    page?: number;
    page_size?: number;
    sort?: string;
    order?: string;
  }) => {
    const res = await api.get<PaginatedResponse<AccountSummary>>('/api/v1/accounts', { params });
    return res.data;
  },
  getAccountDetail: async (accountId: string) => {
    const res = await api.get<ApiResponse<AccountDetail>>(`/api/v1/accounts/${accountId}`);
    return res.data.data;
  },
  getAccountTransactions: async (
    accountId: string,
    params?: { direction?: string; page?: number; page_size?: number }
  ) => {
    const res = await api.get<PaginatedResponse<AccountTransactionItem>>(
      `/api/v1/accounts/${accountId}/transactions`,
      { params }
    );
    return res.data;
  },
  getAccountGraph: async (accountId: string, depth: number = 2) => {
    const res = await api.get<ApiResponse<GraphPayload>>(
      `/api/v1/accounts/${accountId}/graph?depth=${depth}`
    );
    return res.data.data;
  },
  freezeAccount: async (accountId: string, freeze: boolean, reason?: string) => {
    const res = await api.post<ApiResponse<any>>(`/api/v1/accounts/${accountId}/freeze`, {
      freeze,
      reason,
    });
    return res.data.data;
  },

  // Graph Neighborhood
  getGraphNeighborhood: async (accountId: string, hops: number = 2) => {
    const res = await api.get<GraphPayload>(`/api/v1/graph/neighborhood/${accountId}?hops=${hops}`);
    return res.data;
  },
  getSuspiciousNeighborhood: async (accountId: string, minRisk: number = 60.0) => {
    const res = await api.get<GraphPayload>(`/api/v1/graph/suspicious-neighborhood/${accountId}?min_risk=${minRisk}`);
    return res.data;
  },
  getCommonCounterparties: async (accountA: string, accountB: string) => {
    const res = await api.get<any>(`/api/v1/graph/common-counterparties?account_a=${accountA}&account_b=${accountB}`);
    return res.data;
  },

  // Cases Management
  listCases: async (params?: {
    status?: string;
    priority?: string;
    assigned_to?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    const res = await api.get<CaseListResponse>('/api/v1/cases', { params });
    return res.data;
  },
  getCaseDetail: async (caseId: string) => {
    const res = await api.get<InvestigationCase>(`/api/v1/cases/${caseId}`);
    return res.data;
  },
  createCase: async (payload: CaseCreateRequest) => {
    const res = await api.post<InvestigationCase>('/api/v1/cases', payload);
    return res.data;
  },
  updateCase: async (caseId: string, payload: CaseUpdateRequest) => {
    const res = await api.patch<InvestigationCase>(`/api/v1/cases/${caseId}`, payload);
    return res.data;
  },
  assignInvestigator: async (caseId: string, investigator: string) => {
    const res = await api.post<InvestigationCase>(`/api/v1/cases/${caseId}/assign`, {
      assigned_investigator: investigator,
    });
    return res.data;
  },
  addCaseNote: async (caseId: string, content: string) => {
    const res = await api.post<InvestigationNote>(`/api/v1/cases/${caseId}/notes`, { content });
    return res.data;
  },
  attachEvidence: async (caseId: string, payload: any) => {
    const res = await api.post<EvidenceItem>(`/api/v1/cases/${caseId}/evidence`, payload);
    return res.data;
  },
  linkAlertToCase: async (caseId: string, alertId: string) => {
    const res = await api.post<InvestigationCase>(`/api/v1/cases/${caseId}/alerts`, { alert_id: alertId });
    return res.data;
  },
  unlinkAlertFromCase: async (caseId: string, alertId: string) => {
    const res = await api.delete<InvestigationCase>(`/api/v1/cases/${caseId}/alerts/${alertId}`);
    return res.data;
  },
  linkAccountToCase: async (caseId: string, accountId: string) => {
    const res = await api.post<InvestigationCase>(`/api/v1/cases/${caseId}/accounts`, { account_id: accountId });
    return res.data;
  },
  unlinkAccountFromCase: async (caseId: string, accountId: string) => {
    const res = await api.delete<InvestigationCase>(`/api/v1/cases/${caseId}/accounts/${accountId}`);
    return res.data;
  },
  getCaseTimeline: async (caseId: string) => {
    const res = await api.get<InvestigationTimelineResponse>(`/api/v1/cases/${caseId}/timeline`);
    return res.data;
  },

  // Intelligence & Explainability
  getEntityRiskProfile: async (entityId: string, entityType: string = 'ACCOUNT') => {
    const res = await api.get<EntityRiskProfile>(`/api/v1/entities/${entityId}/risk-profile?entity_type=${entityType}`);
    return res.data;
  },
  getEntityRiskExplanation: async (entityId: string) => {
    const res = await api.get<RiskExplanationResponse>(`/api/v1/entities/${entityId}/risk-explanation`);
    return res.data;
  },
  getEntityTimeline: async (entityId: string) => {
    const res = await api.get<InvestigationTimelineResponse>(`/api/v1/entities/${entityId}/timeline`);
    return res.data;
  },
  getInvestigationAnalytics: async () => {
    const res = await api.get<InvestigationAnalytics>('/api/v1/investigation/analytics');
    return res.data;
  },

  // Money Trail & Search
  traceMoneyTrail: async (fromAccount: string, toAccount?: string, maxDepth: number = 4) => {
    const params: any = { from_account: fromAccount, max_depth: maxDepth };
    if (toAccount) params.to_account = toAccount;
    const res = await api.get<ApiResponse<MoneyTrailPath[]>>('/api/v1/investigation/money-trail', {
      params,
    });
    return res.data.data;
  },
  searchEntities: async (query: string) => {
    const res = await api.get<ApiResponse<SearchResults>>('/api/v1/investigation/search', {
      params: { q: query },
    });
    return res.data.data;
  },

  // Fraud Networks & Syndicates (Phase 12)
  listNetworks: async (params?: any) => {
    const res = await api.get<NetworkListResponse>('/api/v1/networks', { params });
    return res.data;
  },
  discoverNetworks: async (forceRefresh: boolean = true) => {
    const res = await api.post<NetworkSummary[]>('/api/v1/networks/discover', null, {
      params: { force_refresh: forceRefresh },
    });
    return res.data;
  },
  getNetworkDetail: async (networkId: string) => {
    const res = await api.get<NetworkDetail>(`/api/v1/networks/${networkId}`);
    return res.data;
  },
  getNetworkMembers: async (networkId: string) => {
    const res = await api.get<NetworkMemberResponse>(`/api/v1/networks/${networkId}/members`);
    return res.data;
  },
  getNetworkSubgraph: async (networkId: string) => {
    const res = await api.get<GraphPayload>(`/api/v1/networks/${networkId}/subgraph`);
    return res.data;
  },
  getNetworkRiskExplanation: async (networkId: string) => {
    const res = await api.get<NetworkRiskExplanationResponse>(`/api/v1/networks/${networkId}/risk-explanation`);
    return res.data;
  },
  getNetworkEvidence: async (networkId: string) => {
    const res = await api.get<NetworkEvidenceResponse>(`/api/v1/networks/${networkId}/evidence`);
    return res.data;
  },
  promoteNetworkToCase: async (networkId: string, req: NetworkCreateCaseRequest) => {
    const res = await api.post<InvestigationCase>(`/api/v1/networks/${networkId}/create-case`, req);
    return res.data;
  },

  // Behavioral Anomaly & Similarity (Phase 12)
  getEntityBehavior: async (entityId: string, window: string = '24h') => {
    const res = await api.get<EntityBehaviorResponse>(`/api/v1/entities/${entityId}/behavior`, {
      params: { window },
    });
    return res.data;
  },
  getEntityBaseline: async (entityId: string) => {
    const res = await api.get<EntityBehaviorBaseline>(`/api/v1/entities/${entityId}/baseline`);
    return res.data;
  },
  getSimilarEntities: async (entityId: string, topK: number = 5) => {
    const res = await api.get<EntitySimilarityResponse>(`/api/v1/entities/${entityId}/similar`, {
      params: { top_k: topK },
    });
    return res.data;
  },

  // ML Feature Store & Generation (Phase 12)
  getFeatureCatalog: async () => {
    const res = await api.get<FeatureDefinition[]>('/api/v1/features/catalog');
    return res.data;
  },
  getEntityFeatures: async (entityId: string) => {
    const res = await api.get<EntityFeatureVector>(`/api/v1/features/entity/${entityId}`);
    return res.data;
  },
  exportFeatureStore: async (req: FeatureStoreExportRequest) => {
    const res = await api.post<FeatureStoreExportResponse>('/api/v1/features/export', req);
    return res.data;
  },

  // Operations & Alert Prioritization (Phase 13)
  listPrioritizedAlerts: async (params?: any) => {
    const res = await api.get<PrioritizedAlertListResponse>('/api/v1/operations/alerts', { params });
    return res.data;
  },
  getInvestigatorQueue: async (params?: any) => {
    const res = await api.get<PrioritizedAlertListResponse>('/api/v1/operations/queue', { params });
    return res.data;
  },
  getAlertPriorityExplanation: async (alertId: string) => {
    const res = await api.get<AlertPriorityExplanation>(`/api/v1/operations/alerts/${alertId}/priority-explanation`);
    return res.data;
  },
  triageAlert: async (alertId: string, payload: AlertTriageRequest) => {
    const res = await api.post<PrioritizedAlert>(`/api/v1/operations/alerts/${alertId}/triage`, payload);
    return res.data;
  },
  assignAlert: async (alertId: string, payload: AlertAssignRequest) => {
    const res = await api.post<PrioritizedAlert>(`/api/v1/operations/alerts/${alertId}/assign`, payload);
    return res.data;
  },
  unassignAlert: async (alertId: string) => {
    const res = await api.post<PrioritizedAlert>(`/api/v1/operations/alerts/${alertId}/unassign`);
    return res.data;
  },
  bulkTriageAlerts: async (payload: BulkAlertTriageRequest) => {
    const res = await api.post<BulkOperationResult>('/api/v1/operations/alerts/bulk-triage', payload);
    return res.data;
  },
  bulkAssignAlerts: async (payload: BulkAlertAssignRequest) => {
    const res = await api.post<BulkOperationResult>('/api/v1/operations/alerts/bulk-assign', payload);
    return res.data;
  },
  getInvestigatorWorkload: async (investigatorId?: string) => {
    const params = investigatorId ? { investigator_id: investigatorId } : {};
    const res = await api.get<WorkloadListResponse>('/api/v1/operations/workload', { params });
    return res.data;
  },
  getSLASummary: async () => {
    const res = await api.get<SLASummary>('/api/v1/operations/sla');
    return res.data;
  },
  getFraudTrends: async (interval: string = 'hourly', days: number = 7) => {
    const res = await api.get<FraudTrendsResponse>('/api/v1/operations/trends', {
      params: { interval, days },
    });
    return res.data;
  },
  getDetectorPerformance: async () => {
    const res = await api.get<DetectorPerformanceResponse>('/api/v1/operations/detectors');
    return res.data;
  },
  getOperationsSummary: async () => {
    const res = await api.get<OperationsSummary>('/api/v1/operations/summary');
    return res.data;
  },
  unifiedSearch: async (q: string, entityTypes?: string[], limit: number = 20, page: number = 1) => {
    const params: any = { q, limit, page };
    if (entityTypes && entityTypes.length > 0) {
      params.entity_types = entityTypes;
    }
    const res = await api.get<UnifiedSearchResponse>('/api/v1/operations/search', { params });
    return res.data;
  },

  // Notifications (Phase 13)
  listNotifications: async (limit: number = 50) => {
    const res = await api.get<NotificationListResponse>('/api/v1/notifications', { params: { limit } });
    return res.data;
  },
  markNotificationRead: async (notificationId: string) => {
    const res = await api.post<AppNotification>(`/api/v1/notifications/${notificationId}/read`);
    return res.data;
  },
  markAllNotificationsRead: async () => {
    const res = await api.post<{ marked_read_count: number }>('/api/v1/notifications/read-all');
    return res.data;
  },

  // Phase 15: Case Intelligence & Collaboration
  getCaseCorrelations: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseCorrelationResponse>>(`/api/v1/case-intelligence/cases/${caseId}/related`);
    return res.data;
  },
  getCaseRelationshipGraph: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseRelationshipGraph>>(`/api/v1/case-intelligence/cases/${caseId}/graph`);
    return res.data;
  },
  getCaseEvidenceProvenance: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseEvidenceProvenanceResponse>>(`/api/v1/case-intelligence/cases/${caseId}/evidence-provenance`);
    return res.data;
  },
  getCaseActivityFeed: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseActivityEvent[]>>(`/api/v1/case-intelligence/cases/${caseId}/activity`);
    return res.data;
  },
  listCaseCollaborators: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseCollaborator[]>>(`/api/v1/case-intelligence/cases/${caseId}/collaborators`);
    return res.data;
  },
  addCaseCollaborator: async (caseId: string, req: AddCollaboratorRequest) => {
    const res = await api.post<ApiResponse<CaseCollaborator>>(`/api/v1/case-intelligence/cases/${caseId}/collaborators`, req);
    return res.data;
  },
  removeCaseCollaborator: async (caseId: string, userId: string) => {
    const res = await api.delete<ApiResponse<{ success: boolean }>>(`/api/v1/case-intelligence/cases/${caseId}/collaborators/${userId}`);
    return res.data;
  },
  listCaseComments: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseComment[]>>(`/api/v1/case-intelligence/cases/${caseId}/comments`);
    return res.data;
  },
  addCaseComment: async (caseId: string, req: AddCommentRequest) => {
    const res = await api.post<ApiResponse<CaseComment>>(`/api/v1/case-intelligence/cases/${caseId}/comments`, req);
    return res.data;
  },
  updateCaseComment: async (caseId: string, commentId: string, req: UpdateCommentRequest) => {
    const res = await api.patch<ApiResponse<CaseComment>>(`/api/v1/case-intelligence/cases/${caseId}/comments/${commentId}`, req);
    return res.data;
  },
  deleteCaseComment: async (caseId: string, commentId: string) => {
    const res = await api.delete<ApiResponse<{ success: boolean }>>(`/api/v1/case-intelligence/cases/${caseId}/comments/${commentId}`);
    return res.data;
  },
  listCampaigns: async (status?: string) => {
    const params = status ? { status } : {};
    const res = await api.get<ApiResponse<Campaign[]>>('/api/v1/case-intelligence/campaigns', { params });
    return res.data;
  },
  getCampaign: async (campaignId: string) => {
    const res = await api.get<ApiResponse<Campaign>>(`/api/v1/case-intelligence/campaigns/${campaignId}`);
    return res.data;
  },
  updateCampaign: async (campaignId: string, req: CampaignUpdateRequest) => {
    const res = await api.patch<ApiResponse<Campaign>>(`/api/v1/case-intelligence/campaigns/${campaignId}`, req);
    return res.data;
  },
  getCampaignCases: async (campaignId: string) => {
    const res = await api.get<ApiResponse<InvestigationCaseSummary[]>>(`/api/v1/case-intelligence/campaigns/${campaignId}/cases`);
    return res.data;
  },
  getCampaignExplanation: async (campaignId: string) => {
    const res = await api.get<ApiResponse<CampaignRiskExplanation>>(`/api/v1/case-intelligence/campaigns/${campaignId}/explanation`);
    return res.data;
  },
  getCommandCenterSummary: async () => {
    const res = await api.get<ApiResponse<CommandCenterSummary>>('/api/v1/case-intelligence/command-center/summary');
    return res.data;
  },
  getEnterpriseFraudPosture: async () => {
    const res = await api.get<ApiResponse<EnterpriseFraudPosture>>('/api/v1/case-intelligence/command-center/posture');
    return res.data;
  },

  // Phase 16: Advanced Graph Intelligence & Predictive Risk
  getNetworkEvolution: async (networkId: string, window: string = '1h') => {
    const res = await api.get<ApiResponse<NetworkEvolutionSnapshot>>(`/api/v1/advanced-intelligence/networks/${networkId}/evolution`, { params: { window } });
    return res.data;
  },
  getNetworkTrajectory: async (networkId: string) => {
    const res = await api.get<ApiResponse<any>>(`/api/v1/advanced-intelligence/networks/${networkId}/trajectory`);
    return res.data;
  },
  getNetworkForecast: async (networkId: string) => {
    const res = await api.get<ApiResponse<NetworkRiskForecast>>(`/api/v1/advanced-intelligence/networks/${networkId}/forecast`);
    return res.data;
  },
  getEntityTrajectory: async (entityType: string, entityId: string) => {
    const res = await api.get<ApiResponse<EntityRiskTrajectory>>(`/api/v1/advanced-intelligence/entities/${entityType}/${entityId}/trajectory`);
    return res.data;
  },
  listEmergingNetworks: async () => {
    const res = await api.get<ApiResponse<EmergingNetwork[]>>('/api/v1/advanced-intelligence/emerging-networks');
    return res.data;
  },
  listEarlyWarnings: async (params?: { severity?: string; status?: string; entity_type?: string }) => {
    const res = await api.get<ApiResponse<EarlyWarning[]>>('/api/v1/advanced-intelligence/early-warnings', { params });
    return res.data;
  },
  getEarlyWarning: async (warningId: string) => {
    const res = await api.get<ApiResponse<EarlyWarning>>(`/api/v1/advanced-intelligence/early-warnings/${warningId}`);
    return res.data;
  },
  acknowledgeEarlyWarning: async (warningId: string, req: EarlyWarningActionRequest) => {
    const res = await api.post<ApiResponse<EarlyWarning>>(`/api/v1/advanced-intelligence/early-warnings/${warningId}/acknowledge`, req);
    return res.data;
  },
  escalateEarlyWarning: async (warningId: string, req: EarlyWarningActionRequest) => {
    const res = await api.post<ApiResponse<EarlyWarning>>(`/api/v1/advanced-intelligence/early-warnings/${warningId}/escalate`, req);
    return res.data;
  },
  dismissEarlyWarning: async (warningId: string, req: EarlyWarningActionRequest) => {
    const res = await api.post<ApiResponse<EarlyWarning>>(`/api/v1/advanced-intelligence/early-warnings/${warningId}/dismiss`, req);
    return res.data;
  },
  listDiscoveredPatterns: async (patternType?: string) => {
    const params = patternType ? { pattern_type: patternType } : {};
    const res = await api.get<ApiResponse<DiscoveredPattern[]>>('/api/v1/advanced-intelligence/patterns', { params });
    return res.data;
  },
  getDiscoveredPattern: async (patternId: string) => {
    const res = await api.get<ApiResponse<DiscoveredPattern>>(`/api/v1/advanced-intelligence/patterns/${patternId}`);
    return res.data;
  },
  getSimilarPatterns: async (patternId: string) => {
    const res = await api.get<ApiResponse<PatternSimilarityResponse[]>>(`/api/v1/advanced-intelligence/patterns/${patternId}/similar`);
    return res.data;
  },
  getEnterpriseThreatLevel: async () => {
    const res = await api.get<ApiResponse<EnterpriseThreatAssessment>>('/api/v1/advanced-intelligence/threat-level');
    return res.data;
  },
  getEnterpriseThreatHistory: async () => {
    const res = await api.get<ApiResponse<any[]>>('/api/v1/advanced-intelligence/threat-level/history');
    return res.data;
  },
  getEnterpriseRiskForecast: async () => {
    const res = await api.get<ApiResponse<EnterpriseRiskForecast>>('/api/v1/advanced-intelligence/enterprise-forecast');
    return res.data;
  },
  getCommandCenterAdvancedSummary: async () => {
    const res = await api.get<ApiResponse<any>>('/api/v1/advanced-intelligence/command-center/advanced-summary');
    return res.data;
  },

  // Phase 17: Autonomous Intelligence, Shadow Detection, Risk Calibration & Threat Propagation
  getAutonomousSummary: async () => {
    const res = await api.get<ApiResponse<AutonomousIntelligenceSummary>>('/api/v1/autonomous-intelligence/summary');
    return res.data;
  },
  listDetectionGaps: async (priority?: string) => {
    const params = priority ? { priority } : {};
    const res = await api.get<ApiResponse<DetectionGap[]>>('/api/v1/autonomous-intelligence/gaps', { params });
    return res.data;
  },
  getDetectionGap: async (gapId: string) => {
    const res = await api.get<ApiResponse<DetectionGap>>(`/api/v1/autonomous-intelligence/gaps/${gapId}`);
    return res.data;
  },
  triggerDetectionGapScan: async () => {
    const res = await api.post<ApiResponse<DetectionGap[]>>('/api/v1/autonomous-intelligence/gaps/scan');
    return res.data;
  },
  listDetectorRecommendations: async (params?: { status?: string; rec_type?: string }) => {
    const res = await api.get<ApiResponse<DetectorRecommendation[]>>('/api/v1/autonomous-intelligence/recommendations', { params });
    return res.data;
  },
  getDetectorRecommendation: async (recId: string) => {
    const res = await api.get<ApiResponse<DetectorRecommendation>>(`/api/v1/autonomous-intelligence/recommendations/${recId}`);
    return res.data;
  },
  reviewDetectorRecommendation: async (recId: string, req: RecommendationReviewRequest) => {
    const res = await api.post<ApiResponse<DetectorRecommendation>>(`/api/v1/autonomous-intelligence/recommendations/${recId}/review`, req);
    return res.data;
  },
  listDetectorVersions: async (detectorId?: string) => {
    const params = detectorId ? { detector_id: detectorId } : {};
    const res = await api.get<ApiResponse<DetectorVersion[]>>('/api/v1/autonomous-intelligence/detector-versions', { params });
    return res.data;
  },
  runShadowSimulation: async (req: ShadowSimulationRequest) => {
    const res = await api.post<ApiResponse<ShadowSimulationResult>>('/api/v1/autonomous-intelligence/shadow/simulate', req);
    return res.data;
  },
  listShadowSimulations: async (detectorId?: string) => {
    const params = detectorId ? { detector_id: detectorId } : {};
    const res = await api.get<ApiResponse<ShadowSimulationResult[]>>('/api/v1/autonomous-intelligence/shadow/simulations', { params });
    return res.data;
  },
  getShadowSimulation: async (simId: string) => {
    const res = await api.get<ApiResponse<ShadowSimulationResult>>(`/api/v1/autonomous-intelligence/shadow/simulations/${simId}`);
    return res.data;
  },
  getRiskCalibrationReport: async (windowDays: number = 30) => {
    const res = await api.get<ApiResponse<RiskCalibrationReport>>('/api/v1/autonomous-intelligence/risk-calibration', { params: { window_days: windowDays } });
    return res.data;
  },
  refreshRiskCalibration: async (windowDays: number = 30) => {
    const res = await api.post<ApiResponse<RiskCalibrationReport>>('/api/v1/autonomous-intelligence/risk-calibration/refresh', null, { params: { window_days: windowDays } });
    return res.data;
  },
  analyzeThreatPropagation: async (req: { origin_entity_id: string; max_hops?: number; time_window_hours?: number }) => {
    const res = await api.post<ApiResponse<ThreatPropagationAnalysis>>('/api/v1/autonomous-intelligence/threat-propagation/analyze', req);
    return res.data;
  },
  getEntityThreatPropagation: async (entityId: string, maxHops: number = 3, timeWindowHours: number = 24) => {
    const res = await api.get<ApiResponse<ThreatPropagationAnalysis>>(`/api/v1/autonomous-intelligence/threat-propagation/entities/${entityId}`, {
      params: { max_hops: maxHops, time_window_hours: timeWindowHours }
    });
    return res.data;
  },


  // Phase 19: Intelligence Orchestration & Investigation Automation
  getAlertCorrelation: async (alertId: string) => {
    const res = await api.get<ApiResponse<CorrelationGroup>>(`/api/v1/orchestration/correlations/${alertId}`);
    return res.data;
  },
  calculateInvestigationPriority: async (req: any) => {
    const res = await api.post<ApiResponse<InvestigationPriorityScore>>('/api/v1/orchestration/priority/calculate', req);
    return res.data;
  },
  getRankedEvidence: async (caseId: string) => {
    const res = await api.get<ApiResponse<RankedEvidenceItem[]>>(`/api/v1/orchestration/evidence/${caseId}`);
    return res.data;
  },
  getInvestigationBrief: async (caseOrAlertId: string) => {
    const res = await api.get<ApiResponse<InvestigationBrief>>(`/api/v1/orchestration/brief/${caseOrAlertId}`);
    return res.data;
  },
  generateInvestigationBrief: async (req: { case_or_alert_id: string; force_refresh?: boolean }) => {
    const res = await api.post<ApiResponse<InvestigationBrief>>('/api/v1/orchestration/brief/generate', req);
    return res.data;
  },
  listWorkflowTemplates: async () => {
    const res = await api.get<ApiResponse<InvestigationWorkflowTemplate[]>>('/api/v1/orchestration/templates');
    return res.data;
  },
  getWorkflowTemplate: async (templateId: string) => {
    const res = await api.get<ApiResponse<InvestigationWorkflowTemplate>>(`/api/v1/orchestration/templates/${templateId}`);
    return res.data;
  },
  transitionCaseWorkflowState: async (caseId: string, req: { to_state: string; notes?: string }) => {
    const res = await api.post<ApiResponse<WorkflowState>>(`/api/v1/orchestration/cases/${caseId}/workflow-state`, req);
    return res.data;
  },
  getCaseWorkflowState: async (caseId: string) => {
    const res = await api.get<ApiResponse<WorkflowState>>(`/api/v1/orchestration/cases/${caseId}/workflow-state`);
    return res.data;
  },
  listInvestigationTasks: async (params?: { case_id?: string; assignee?: string; status?: string }) => {
    const res = await api.get<ApiResponse<InvestigationTask[]>>('/api/v1/orchestration/tasks', { params });
    return res.data;
  },
  createInvestigationTask: async (req: any) => {
    const res = await api.post<ApiResponse<InvestigationTask>>('/api/v1/orchestration/tasks', req);
    return res.data;
  },
  updateInvestigationTask: async (taskId: string, req: any) => {
    const res = await api.put<ApiResponse<InvestigationTask>>(`/api/v1/orchestration/tasks/${taskId}`, req);
    return res.data;
  },
  completeInvestigationTask: async (taskId: string) => {
    const res = await api.post<ApiResponse<InvestigationTask>>(`/api/v1/orchestration/tasks/${taskId}/complete`);
    return res.data;
  },
  getCaseChecklist: async (caseId: string) => {
    const res = await api.get<ApiResponse<CaseChecklistItem[]>>(`/api/v1/orchestration/cases/${caseId}/checklist`);
    return res.data;
  },
  addCaseChecklistItem: async (caseId: string, req: { title: string; order?: number }) => {
    const res = await api.post<ApiResponse<CaseChecklistItem>>(`/api/v1/orchestration/cases/${caseId}/checklist`, req);
    return res.data;
  },
  updateCaseChecklistItem: async (caseId: string, itemId: string, req: { is_completed: boolean }) => {
    const res = await api.put<ApiResponse<CaseChecklistItem>>(`/api/v1/orchestration/cases/${caseId}/checklist/${itemId}`, req);
    return res.data;
  },
  getUnifiedTimeline: async (caseOrEntityId: string, limit: number = 50) => {
    const res = await api.get<ApiResponse<UnifiedTimelineEvent[]>>(`/api/v1/orchestration/timeline/${caseOrEntityId}`, { params: { limit } });
    return res.data;
  },
  discoverRelatedCases: async (caseId: string) => {
    const res = await api.get<ApiResponse<RelatedCase[]>>(`/api/v1/orchestration/related-cases/${caseId}`);
    return res.data;
  },
  getInvestigationRecommendations: async (caseId: string) => {
    const res = await api.get<ApiResponse<InvestigationRecommendation[]>>(`/api/v1/orchestration/recommendations/${caseId}`);
    return res.data;
  },
  searchInvestigationEntities: async (query: string) => {
    const res = await api.get<ApiResponse<any>>('/api/v1/orchestration/search', { params: { q: query } });
    return res.data;
  },


  // Phase 20 Control Plane & Multi-Tenancy APIs
  getControlPlaneOverview: async (): Promise<ApiResponse<ControlPlaneOverview>> => {
    const res = await api.get('/api/v1/control-plane/overview');
    return res.data;
  },
  listTenants: async (): Promise<ApiResponse<Tenant[]>> => {
    const res = await api.get('/api/v1/control-plane/tenants');
    return res.data;
  },
  createTenant: async (payload: { name: string; slug: string; quotas?: TenantQuota }): Promise<ApiResponse<Tenant>> => {
    const res = await api.post('/api/v1/control-plane/tenants', payload);
    return res.data;
  },
  getTenant: async (tenantId: string): Promise<ApiResponse<Tenant>> => {
    const res = await api.get(`/api/v1/control-plane/tenants/${tenantId}`);
    return res.data;
  },
  updateTenant: async (tenantId: string, payload: { name?: string; quotas?: TenantQuota }): Promise<ApiResponse<Tenant>> => {
    const res = await api.put(`/api/v1/control-plane/tenants/${tenantId}`, payload);
    return res.data;
  },
  transitionTenantStatus: async (tenantId: string, targetStatus: TenantStatus, reason: string): Promise<ApiResponse<Tenant>> => {
    const res = await api.post(`/api/v1/control-plane/tenants/${tenantId}/status`, { target_status: targetStatus, reason });
    return res.data;
  },
  getTenantConfiguration: async (tenantId: string): Promise<ApiResponse<TenantConfiguration>> => {
    const res = await api.get(`/api/v1/control-plane/tenants/${tenantId}/configuration`);
    return res.data;
  },
  listConfigurationVersions: async (tenantId: string): Promise<ApiResponse<ConfigurationVersion[]>> => {
    const res = await api.get(`/api/v1/control-plane/tenants/${tenantId}/configuration/versions`);
    return res.data;
  },
  activateConfigurationVersion: async (tenantId: string, versionId: string): Promise<ApiResponse<ConfigurationVersion>> => {
    const res = await api.post(`/api/v1/control-plane/tenants/${tenantId}/configuration/${versionId}/activate`);
    return res.data;
  },
  getTenantQuotas: async (tenantId: string): Promise<ApiResponse<TenantQuota>> => {
    const res = await api.get(`/api/v1/control-plane/tenants/${tenantId}/quotas`);
    return res.data;
  },
  getTenantUsage: async (tenantId: string): Promise<ApiResponse<TenantUsageMetrics>> => {
    const res = await api.get(`/api/v1/control-plane/tenants/${tenantId}/usage`);
    return res.data;
  },
  listOrganizations: async (): Promise<ApiResponse<Organization[]>> => {
    const res = await api.get('/api/v1/control-plane/organizations');
    return res.data;
  },
  createOrganization: async (payload: { name: string; description?: string }): Promise<ApiResponse<Organization>> => {
    const res = await api.post('/api/v1/control-plane/organizations', payload);
    return res.data;
  },
  listBusinessUnits: async (orgId?: string): Promise<ApiResponse<BusinessUnit[]>> => {
    const res = await api.get('/api/v1/control-plane/business-units', { params: { org_id: orgId } });
    return res.data;
  },
  listTeams: async (): Promise<ApiResponse<InvestigationTeam[]>> => {
    const res = await api.get('/api/v1/control-plane/teams');
    return res.data;
  },
  createTeam: async (payload: { org_id: string; name: string; description?: string; lead_user_id?: string }): Promise<ApiResponse<InvestigationTeam>> => {
    const res = await api.post('/api/v1/control-plane/teams', payload);
    return res.data;
  },
  getTeam: async (teamId: string): Promise<ApiResponse<InvestigationTeam>> => {
    const res = await api.get(`/api/v1/control-plane/teams/${teamId}`);
    return res.data;
  },
  addTeamMember: async (teamId: string, payload: { user_id: string; username: string; role: string }): Promise<ApiResponse<InvestigationTeam>> => {
    const res = await api.post(`/api/v1/control-plane/teams/${teamId}/members`, payload);
    return res.data;
  },
  removeTeamMember: async (teamId: string, userId: string): Promise<ApiResponse<InvestigationTeam>> => {
    const res = await api.delete(`/api/v1/control-plane/teams/${teamId}/members/${userId}`);
    return res.data;
  },
  listTenantUsers: (): Promise<ApiResponse<UserResponse[]>> => {
    return api.get('/api/v1/control-plane/users').then(r => r.data);
  },
  inviteUser: (payload: { username: string; password: string; role: Role; tenant_id?: string; organization_id?: string }): Promise<ApiResponse<UserResponse>> => {
    return api.post('/api/v1/control-plane/users/invite', payload).then(r => r.data);
  },
  updateUserStatus: (userId: string, targetStatus: string, reason?: string): Promise<ApiResponse<UserResponse>> => {
    return api.post(`/api/v1/control-plane/users/${userId}/status`, { target_status: targetStatus, reason }).then(r => r.data);
  },
  listRoles: (): Promise<ApiResponse<Array<{ role: string; description: string }>>> => {
    return api.get('/api/v1/control-plane/roles').then(r => r.data);
  },
  listPermissions: (): Promise<ApiResponse<string[]>> => {
    return api.get('/api/v1/control-plane/permissions').then(r => r.data);
  },
  listPolicies: (): Promise<ApiResponse<Policy[]>> => {
    return api.get('/api/v1/control-plane/policies').then(r => r.data);
  },
  createPolicy: (payload: { name: string; resource: string; action: string; effect: PolicyEffect; priority?: number; description?: string }): Promise<ApiResponse<Policy>> => {
    return api.post('/api/v1/control-plane/policies', payload).then(r => r.data);
  },
  getPolicy: (policyId: string): Promise<ApiResponse<Policy>> => {
    return api.get(`/api/v1/control-plane/policies/${policyId}`).then(r => r.data);
  },
  updatePolicy: (policyId: string, payload: Partial<Policy>): Promise<ApiResponse<Policy>> => {
    return api.put(`/api/v1/control-plane/policies/${policyId}`, payload).then(r => r.data);
  },
  deletePolicy: (policyId: string): Promise<ApiResponse<boolean>> => {
    return api.delete(`/api/v1/control-plane/policies/${policyId}`).then(r => r.data);
  },
  evaluatePolicy: (payload: PolicyEvaluationRequest): Promise<ApiResponse<PolicyEvaluationResult>> => {
    return api.post('/api/v1/control-plane/policies/evaluate', payload).then(r => r.data);
  },
  getTenantAuditLogs: (params?: { action?: string; resource_type?: string; user_id?: string; page?: number; page_size?: number }): Promise<ApiResponse<AuditLog[]>> => {
    return api.get('/api/v1/control-plane/audit', { params }).then(r => r.data);
  },

};

export const apiService = apiClient;
