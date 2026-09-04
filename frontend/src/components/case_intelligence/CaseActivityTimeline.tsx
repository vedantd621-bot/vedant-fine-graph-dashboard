import React from 'react';
import { History, CheckCircle, UserPlus, AlertCircle, FileText, ArrowRight } from 'lucide-react';
import { CaseActivityEvent } from '../../types';

interface CaseActivityTimelineProps {
  activities: CaseActivityEvent[];
}

export const CaseActivityTimeline: React.FC<CaseActivityTimelineProps> = ({ activities }) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'CASE_CREATED':
        return <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />;
      case 'COLLABORATOR_ADDED':
      case 'COLLABORATOR_REMOVED':
        return <UserPlus className="h-3.5 w-3.5 text-cyan-400" />;
      case 'COMMENT_ADDED':
      case 'COMMENT_UPDATED':
      case 'COMMENT_DELETED':
        return <FileText className="h-3.5 w-3.5 text-blue-400" />;
      case 'CASE_STATUS_CHANGED':
      case 'CASE_REASSIGNED':
        return <ArrowRight className="h-3.5 w-3.5 text-amber-400" />;
      default:
        return <AlertCircle className="h-3.5 w-3.5 text-purple-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <History className="h-4 w-4 text-cyan-400" />
        <span>Investigation Activity Feed</span>
      </div>

      <div className="relative pl-4 border-l border-slate-800 space-y-3 text-xs">
        {activities.map((act) => (
          <div key={act.event_id} className="relative group">
            <div className="absolute -left-[21px] top-0.5 p-0.5 rounded-full bg-slate-900 border border-slate-700">
              {getEventIcon(act.event_type)}
            </div>
            <div className="space-y-0.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="font-semibold text-slate-300">{act.actor_name}</span>
                <span className="text-[10px] text-slate-500">
                  {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-slate-300">{act.summary}</p>
            </div>
          </div>
        ))}
        {activities.length === 0 && (
          <div className="text-xs text-slate-500 italic">No activity recorded.</div>
        )}
      </div>
    </div>
  );
};
