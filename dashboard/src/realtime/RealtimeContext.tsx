import React, { createContext, useContext, useEffect, useState } from 'react';
import { AlertCreatedData, ConnectionStatus, RealtimeEvent } from '../types/realtime';
import { realtimeClient } from './websocket';

interface RealtimeContextType {
  status: ConnectionStatus;
  recentEvents: RealtimeEvent[];
  notifications: AlertCreatedData[];
  activeToast: AlertCreatedData | null;
  lastEventTime: Date | null;
  dismissToast: () => void;
  clearNotifications: () => void;
  watchAccount: (accountId: string) => void;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

export const RealtimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<ConnectionStatus>(realtimeClient.getStatus());
  const [recentEvents, setRecentEvents] = useState<RealtimeEvent[]>([]);
  const [notifications, setNotifications] = useState<AlertCreatedData[]>([]);
  const [activeToast, setActiveToast] = useState<AlertCreatedData | null>(null);
  const [lastEventTime, setLastEventTime] = useState<Date | null>(null);

  useEffect(() => {
    const unsubStatus = realtimeClient.onStatusChange((newStatus) => {
      setStatus(newStatus);
    });

    realtimeClient.connect();

    const unsubAll = realtimeClient.on('*', (evt) => {
      setLastEventTime(new Date());
      if (evt.event !== 'system.ping' && evt.event !== 'system.pong') {
        setRecentEvents((prev) => [evt, ...prev.slice(0, 49)]);
      }
    });

    const unsubAlert = realtimeClient.on('alert.created', (evt) => {
      const data: AlertCreatedData = evt.data;
      setNotifications((prev) => [data, ...prev.slice(0, 29)]);
      setActiveToast(data);

      setTimeout(() => {
        setActiveToast((current) => (current?.alert_id === data.alert_id ? null : current));
      }, 6000);
    });

    return () => {
      unsubStatus();
      unsubAll();
      unsubAlert();
      realtimeClient.disconnect();
    };
  }, []);

  const dismissToast = () => {
    setActiveToast(null);
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const watchAccount = (accountId: string) => {
    realtimeClient.watchAccount(accountId);
  };

  return (
    <RealtimeContext.Provider
      value={{
        status,
        recentEvents,
        notifications,
        activeToast,
        lastEventTime,
        dismissToast,
        clearNotifications,
        watchAccount,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
};

export const useRealtime = (): RealtimeContextType => {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
};
