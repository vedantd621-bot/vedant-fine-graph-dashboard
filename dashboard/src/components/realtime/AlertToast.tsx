import React from 'react';
import { ShieldAlert, X, ArrowRight } from 'lucide-react';
import { useRealtime } from '../../realtime/RealtimeContext';

interface AlertToastProps {
  onSelectAlert?: (alertId: string) => void;
}

export const AlertToast: React.FC<AlertToastProps> = ({ onSelectAlert }) => {
  const { activeToast, dismissToast } = useRealtime();

  if (!activeToast) return null;

  const isCrit = activeToast.severity === 'CRITICAL';

  return (
    <div className="fixed top-16 right-6 z-50 max-w-sm w-full animate-bounce-in">
      <div className="p-4 rounded-xl bg-slate-900/95 border border-rose-500/40 shadow-2xl shadow-rose-950/50 backdrop-blur text-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping"></span>
            <ShieldAlert className="h-4 w-4 text-rose-400" />
            <span className="font-bold uppercase tracking-wider text-rose-300 text-[11px]">
              New Fraud Alert Detected
            </span>
          </div>
          <button
            onClick={dismissToast}
            className="text-slate-400 hover:text-slate-200 p-0.5 rounded transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="text-slate-100 font-semibold">{activeToast.description}</div>

        <div className="flex items-center justify-between text-[11px] text-slate-300 pt-1">
          <div>
            Account: <span className="font-mono text-cyan-400 font-bold">{activeToast.primary_account}</span>
          </div>
          <span
            className={`font-bold px-2 py-0.5 rounded text-[10px] uppercase border ${
              isCrit
                ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            }`}
          >
            {activeToast.severity}
          </span>
        </div>

        <div className="pt-2 flex items-center justify-end">
          <button
            onClick={() => {
              if (onSelectAlert) onSelectAlert(activeToast.alert_id);
              dismissToast();
            }}
            className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1 transition-colors"
          >
            Investigate Alert <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
