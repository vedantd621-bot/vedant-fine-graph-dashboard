export type NotificationType =
  | 'CRITICAL_ALERT'
  | 'SLA_WARNING'
  | 'SLA_BREACH'
  | 'ALERT_ASSIGNED'
  | 'ALERT_REASSIGNED'
  | 'CASE_ESCALATED'
  | 'NETWORK_DISCOVERY'
  | 'SYSTEM_NOTICE';

export type NotificationSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface AppNotification {
  notification_id: string;
  user_id?: string | null;
  target_role?: string | null;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  resource_type?: string | null;
  resource_id?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: AppNotification[];
  unread_count: number;
}
