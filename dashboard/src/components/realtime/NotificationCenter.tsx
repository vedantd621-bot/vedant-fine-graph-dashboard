import React, { useState } from 'react';
import { Bell, ShieldAlert, Activity, Trash2, X, ArrowRight, Radio } from 'lucide-react';
import { useRealtime } from '../../realtime/RealtimeContext';

interface NotificationCenterProps {
  onSelectAlert?: (alertId: string) => void;
  onSelectAccount?: (accountId: string) => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  onSelectAlert,
  onSelectAccount,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'alerts' | 'events'>('alerts');
  const { status, notifications, recentEvents, clearNotifications } = useRealtime();

  const unreadCount = notifications.length;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 transition-colors"
        title="Real-Time Event Center"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-4 min-w-4 px-1 rounded-full bg-rose-500 text-white font-bold text-[10px] flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl z-50 overflow-hidden text-xs">
          <div className="p-3.5 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100">Live Investigation Stream</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                  status === 'LIVE'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : status === 'CONNECTING'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    status === 'LIVE' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-400'
                  }`}
                ></span>
                {status}
              </span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-200 p-0.5 rounded"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="px-3 pt-2 pb-1 bg-slate-900 flex items-center justify-between border-b border-slate-800">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('alerts')}
                className={`pb-1 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'alerts'
                    ? 'border-cyan-400 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Live Alerts ({notifications.length})
              </button>
              <button
                onClick={() => setActiveTab('events')}
                className={`pb-1 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'events'
                    ? 'border-cyan-400 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Raw Events ({recentEvents.length})
              </button>
            </div>

            {notifications.length > 0 && activeTab === 'alerts' && (
              <button
                onClick={clearNotifications}
                className="text-[10px] text-slate-400 hover:text-rose-400 flex items-center gap-1 transition-colors"
              >
                <Trash2 className="h-3 w-3" /> Clear
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60 p-1">
            {activeTab === 'alerts' ? (
              notifications.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No new alerts received in this session.
                </div>
              ) : (
                notifications.map((alt, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      if (onSelectAlert) onSelectAlert(alt.alert_id);
                      setIsOpen(false);
                    }}
                    className="p-2.5 rounded-lg hover:bg-slate-800/50 cursor-pointer transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-cyan-400 font-bold text-[11px]">
                        {alt.alert_id}
                      </span>
                      <span className="text-[10px] font-bold uppercase px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                        {alt.severity}
                      </span>
                    </div>
                    <div className="text-slate-200 font-medium line-clamp-1">{alt.description}</div>
                    <div className="text-[10px] text-slate-400">
                      Target Account: <span className="text-slate-300 font-mono">{alt.primary_account}</span>
                    </div>
                  </div>
                ))
              )
            ) : (
              recentEvents.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  No real-time events logged yet.
                </div>
              ) : (
                recentEvents.map((evt, idx) => (
                  <div key={idx} className="p-2 text-[11px] font-mono hover:bg-slate-800/40">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="text-cyan-300 font-bold">{evt.event}</span>
                      <span className="text-[10px]">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-400 text-[10px] truncate mt-0.5">
                      {JSON.stringify(evt.data)}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
};
