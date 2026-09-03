import axios from 'axios';
import {
  AccountDetail,
  AccountSummary,
  AccountTransactionItem,
  AlertDetail,
  AlertStatus,
  AlertSummary,
  ApiResponse,
  DashboardSummary,
  GraphPayload,
  MoneyTrailPath,
  PaginatedResponse,
  RiskDistribution,
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

  // Investigation
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
};
