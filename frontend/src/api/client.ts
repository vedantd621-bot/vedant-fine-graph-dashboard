import axios from 'axios';
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

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ||
  (window as any).__ENV__?.REACT_APP_API_BASE_URL ||
  'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT token if stored
api.interceptors.request.use((config) => {
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
      localStorage.removeItem('fingraph_token');
      localStorage.removeItem('fingraph_user');
      if (typeof window !== 'undefined' && !window.location.pathname.includes('login')) {
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
};
