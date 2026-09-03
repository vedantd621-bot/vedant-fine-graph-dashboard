import React from 'react';
import {
  LayoutDashboard,
  AlertTriangle,
  Users,
  Compass,
  GitFork,
  Activity,
  Sliders,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  openAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  openAlertsCount = 0,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'alerts', label: 'Alerts Catalog', icon: AlertTriangle, badge: openAlertsCount },
    { id: 'accounts', label: 'Account Dossiers', icon: Users },
    { id: 'investigation', label: 'Forensic Investigation', icon: Compass },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 text-slate-300">
      <div className="space-y-6">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3">
          Investigation Platform
        </div>

        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 ? (
                  <span className="bg-rose-500/20 border border-rose-500/30 text-rose-400 text-[11px] font-bold px-2 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footnote */}
      <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-800 text-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Risk Engine</span>
          <span className="text-cyan-400 font-semibold">rule-gds-v1</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Graph Backend</span>
          <span className="text-emerald-400 font-medium">Neo4j 5.18 GDS</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Pipeline</span>
          <span className="text-slate-300 font-medium">Flink 1.18 KRaft</span>
        </div>
      </div>
    </aside>
  );
};
