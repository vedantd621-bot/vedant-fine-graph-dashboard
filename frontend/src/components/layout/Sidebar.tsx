import React, { useState } from 'react';
import {
  LayoutDashboard,
  BarChart2,
  FileText,
  Share2,
  AlertTriangle,
  Users,
  Compass,
  Shield,
  ShieldAlert,
  ListOrdered,
  Briefcase,
  TrendingUp,
  Zap,
  Activity,
  Layers,
  ChevronDown,
  ChevronRight,
  Search
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
  const [enterpriseExpanded, setEnterpriseExpanded] = useState<boolean>(true);

  // The 6 Primary Core Modules as requested
  const primaryModules = [
    { id: 'dashboard', label: '1. DASHBOARD', icon: LayoutDashboard, badge: undefined },
    { id: 'investigation', label: '2. INVESTIGATION', icon: Compass, badge: undefined },
    { id: 'networks', label: '3. FRAUD NETWORKS', icon: Share2, badge: undefined },
    { id: 'alerts', label: '4. ALERTS', icon: AlertTriangle, badge: openAlertsCount },
    { id: 'analytics-explorer', label: '5. ANALYTICS', icon: BarChart2, badge: undefined },
    { id: 'transaction-detail', label: '6. TRANSACTION DETAILS', icon: FileText, badge: undefined },
  ];

  // Secondary Advanced Enterprise Features (Preserved in full)
  const enterpriseModules = [
    { id: 'control-center', label: 'Control Center', icon: Shield },
    { id: 'reporting-center', label: 'Reporting Center', icon: FileText },
    { id: 'decisioning-sandbox', label: 'Decisioning Sandbox', icon: ShieldAlert },
    { id: 'tenants', label: 'Tenants', icon: LayoutDashboard },
    { id: 'policies', label: 'Policy Engine', icon: ShieldAlert },
    { id: 'user-management', label: 'User Identities', icon: Users },
    { id: 'team-management', label: 'Investigation Teams', icon: Briefcase },
    { id: 'command-center', label: 'Command Center V2', icon: Zap },
    { id: 'early-warnings', label: 'Early Warning Center', icon: AlertTriangle },
    { id: 'network-evolution', label: 'Network Evolution', icon: Activity },
    { id: 'pattern-intelligence', label: 'Pattern Intelligence', icon: Layers },
    { id: 'adaptive-intelligence', label: 'Adaptive Intelligence', icon: Zap },
    { id: 'threat-propagation', label: 'Threat Propagation', icon: Activity },
    { id: 'investigation-intelligence', label: 'Intelligence Workspace', icon: Compass },
    { id: 'alert-correlation', label: 'Alert Correlation', icon: Share2 },
    { id: 'task-management', label: 'Task Management', icon: ListOrdered },
    { id: 'case-intelligence', label: 'Case Intelligence', icon: Share2 },
    { id: 'operations', label: 'Fraud Ops Dashboard', icon: TrendingUp },
    { id: 'queue', label: 'Alert Queue & Triage', icon: ListOrdered },
    { id: 'investigator-hub', label: 'Investigator Workspace', icon: Briefcase },
    { id: 'accounts', label: 'Account Dossiers', icon: Users },
    { id: 'cases', label: 'Case Management', icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 text-slate-300 overflow-y-auto">
      <div className="space-y-6">
        {/* Header Title */}
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 flex items-center justify-between">
          <span>FinGraph Intelligence</span>
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">v2.6</span>
        </div>

        {/* 6 PRIMARY CORE MODULES */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400/90 px-3 mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Core Navigation (6 Modules)
          </div>

          <nav className="space-y-1">
            {primaryModules.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-bold tracking-wide transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 ? (
                    <span className="bg-rose-500/20 border border-rose-500/30 text-rose-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </div>

        {/* SECONDARY ADVANCED ENTERPRISE SUITE (COLLAPSIBLE) */}
        <div className="pt-2 border-t border-slate-800/80 space-y-2">
          <button
            onClick={() => setEnterpriseExpanded(!enterpriseExpanded)}
            className="w-full flex items-center justify-between px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span>Advanced Intelligence ({enterpriseModules.length})</span>
            {enterpriseExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>

          {enterpriseExpanded && (
            <nav className="space-y-1 pl-1">
              {enterpriseModules.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800 text-cyan-400 border-l-2 border-cyan-400 font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                      <span className="truncate">{item.label}</span>
                    </div>
                  </button>
                );
              })}
            </nav>
          )}
        </div>
      </div>

      {/* System Status Footnote */}
      <div className="mt-6 p-3 rounded-xl bg-slate-800/40 border border-slate-800 text-[11px] space-y-1.5 shrink-0">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Engine State</span>
          <span className="text-cyan-400 font-semibold">Active Ready</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Primary Core</span>
          <span className="text-emerald-400 font-medium">6 Modules Live</span>
        </div>
      </div>
    </aside>
  );
};
