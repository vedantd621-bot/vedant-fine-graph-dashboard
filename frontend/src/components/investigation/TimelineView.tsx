import React from 'react';
import {
  Clock,
  Activity,
  AlertTriangle,
  ShieldAlert,
  FileText,
  Lock,
  Compass,
  ArrowRight,
  User,
  Paperclip,
} from 'lucide-react';
import { InvestigationTimelineEvent, TimelineEventType } from '../../types';

interface TimelineViewProps {
  events: InvestigationTimelineEvent[];
  title?: string;
  emptyMessage?: string;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  events,
  title = 'Investigation Timeline',
  emptyMessage = 'No chronological events recorded yet for this entity.',
}) => {
  const getEventIcon = (type: TimelineEventType) => {
    switch (type) {
      case 'TRANSACTION':
        return <Activity className="h-3.5 w-3.5 text-cyan-400" />;
      case 'DETECTOR_MATCH':
        return <Compass className="h-3.5 w-3.5 text-amber-400" />;
      case 'ALERT_CREATED':
        return <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />;
      case 'ACCOUNT_FROZEN':
        return <Lock className="h-3.5 w-3.5 text-rose-500" />;
      case 'CASE_CREATED':
      case 'CASE_UPDATED':
        return <ShieldAlert className="h-3.5 w-3.5 text-indigo-400" />;
      case 'INVESTIGATION_NOTE':
        return <FileText className="h-3.5 w-3.5 text-emerald-400" />;
      case 'EVIDENCE_ATTACHED':
        return <Paperclip className="h-3.5 w-3.5 text-purple-400" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-slate-400" />;
    }
  };

  const getEventBadgeColor = (type: TimelineEventType) => {
    switch (type) {
      case 'TRANSACTION':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'DETECTOR_MATCH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'ALERT_CREATED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'ACCOUNT_FROZEN':
        return 'bg-rose-600/20 text-rose-300 border-rose-600/40';
      case 'CASE_CREATED':
      case 'CASE_UPDATED':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'INVESTIGATION_NOTE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'EVIDENCE_ATTACHED':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  if (!events || events.length === 0) {
    return (
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 text-center space-y-2">
        <Clock className="h-6 w-6 text-slate-600 mx-auto" />
        <p className="text-xs text-slate-400">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {title && (
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Clock className="h-4 w-4 text-cyan-400" />
            {title} ({events.length} Events)
          </h3>
        </div>
      )}

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {events.map((evt, idx) => (
          <div key={evt.event_id || idx} className="relative group">
            {/* Timeline Dot */}
            <div className="absolute -left-6 top-1 h-5 w-5 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center shadow-sm">
              {getEventIcon(evt.event_type)}
            </div>

            {/* Event Content Box */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-colors space-y-1.5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${getEventBadgeColor(
                      evt.event_type
                    )}`}
                  >
                    {evt.event_type.replace('_', ' ')}
                  </span>
                  <span className="text-xs font-bold text-slate-200">{evt.title}</span>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {new Date(evt.timestamp).toLocaleString()}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{evt.description}</p>

              {(evt.actor || evt.evidence_ref) && (
                <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-400 border-t border-slate-800/60 mt-1">
                  {evt.actor && (
                    <span className="flex items-center gap-1 text-slate-300">
                      <User className="h-3 w-3 text-cyan-400" /> Actor: {evt.actor}
                    </span>
                  )}
                  {evt.evidence_ref && (
                    <span className="flex items-center gap-1 font-mono text-cyan-400/90">
                      <Paperclip className="h-3 w-3" /> Ref: {evt.evidence_ref}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
