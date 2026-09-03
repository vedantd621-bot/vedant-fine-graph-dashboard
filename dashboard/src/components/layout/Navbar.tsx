import React, { useState } from 'react';
import { Shield, Search, RefreshCw, Radio } from 'lucide-react';
import { useRealtime } from '../../realtime/RealtimeContext';
import { NotificationCenter } from '../realtime/NotificationCenter';

interface NavbarProps {
  onSearch?: (query: string) => void;
  onRefresh?: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onSelectAlert?: (alertId: string) => void;
  onSelectAccount?: (accountId: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onSearch,
  onRefresh,
  activeTab,
  setActiveTab,
  onSelectAlert,
  onSelectAccount,
}) => {
  const [searchInput, setSearchInput] = useState('');
  const { status, lastEventTime } = useRealtime();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim() && onSearch) {
      onSearch(searchInput.trim());
      setActiveTab('investigation');
    }
  };

  const statusStyles = {
    LIVE: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400',
      dot: 'bg-emerald-400',
      animate: true,
      label: '● LIVE STREAM',
    },
    CONNECTING: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      dot: 'bg-amber-400',
      animate: true,
      label: '● RECONNECTING...',
    },
    DISCONNECTED: {
      bg: 'bg-slate-800',
      border: 'border-slate-700',
      text: 'text-slate-400',
      dot: 'bg-slate-500',
      animate: false,
      label: '● OFFLINE',
    },
  }[status];

  return (
    <header className="bg-slate-900/90 backdrop-blur border-b border-slate-800 sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between text-slate-100">
      <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Shield className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="font-bold text-lg tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-300 bg-clip-text text-transparent">
            FinGraph
          </div>
          <div className="text-[10px] uppercase font-semibold tracking-wider text-slate-400">
            Real-Time Fraud Syndicate Analytics
          </div>
        </div>
      </div>

      <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md mx-8 relative">
        <div className="relative flex items-center">
          <Search className="h-4 w-4 absolute left-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Account (A005), Transaction (TX10001), Alert ID..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
          />
        </div>
      </form>

      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${statusStyles.bg} ${statusStyles.border} ${statusStyles.text}`}
          title={lastEventTime ? `Last stream event: ${lastEventTime.toLocaleTimeString()}` : 'Connected to WebSocket stream'}
        >
          <span
            className={`h-2 w-2 rounded-full ${statusStyles.dot} ${statusStyles.animate ? 'animate-pulse' : ''}`}
          ></span>
          <span>{statusStyles.label}</span>
        </div>

        <NotificationCenter
          onSelectAlert={onSelectAlert}
          onSelectAccount={onSelectAccount}
        />

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Refresh View"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </header>
  );
};
