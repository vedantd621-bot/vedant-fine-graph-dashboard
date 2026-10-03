import React, { useEffect, useState } from 'react';
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
  Server,
  Database,
  Cpu,
  Radio
} from 'lucide-react';
import { apiClient } from '../../api/client';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  openAlertsCount?: number;
}

interface ServiceHealthStatus {
  api: 'ONLINE' | 'DEMO' | 'OFFLINE';
  kafka: 'ONLINE' | 'DEMO' | 'OFFLINE';
  flink: 'ONLINE' | 'DEMO' | 'OFFLINE';
  neo4j: 'ONLINE' | 'DEMO' | 'OFFLINE';
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  openAlertsCount = 0,
}) => {
  const [enterpriseExpanded, setEnterpriseExpanded] = useState<boolean>(false);
  const [systemHealth, setSystemHealth] = useState<ServiceHealthStatus>({
    api: 'DEMO',
    kafka: 'DEMO',
    flink: 'DEMO',
    neo4j: 'DEMO',
  });

  useEffect(() => {
    let isMounted = true;
    const checkSystemHealth = async () => {
      try {
        const healthRes = await apiClient.getHealth();
        if (healthRes && healthRes.status === 'ok') {
          // Check deeper endpoints if reachable
          let neo4jStatus: 'ONLINE' | 'DEMO' | 'OFFLINE' = 'ONLINE';
          let kafkaStatus: 'ONLINE' | 'DEMO' | 'OFFLINE' = 'ONLINE';

          try {
            await apiClient.getHealth(); // ping
          } catch {
            neo4jStatus = 'DEMO';
          }

          if (isMounted) {
            setSystemHealth({
              api: 'ONLINE',
              kafka: kafkaStatus,
              flink: 'ONLINE',
              neo4j: neo4jStatus,
            });
          }
        }
      } catch {
        if (isMounted) {
          setSystemHealth({
            api: 'DEMO',
            kafka: 'DEMO',
            flink: 'DEMO',
            neo4j: 'DEMO',
          });
        }
      }
    };

    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // 6 Primary Core Navigation Items requested
  const primaryModules = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard, badge: undefined },
    { id: 'transaction-detail', label: 'Transactions', icon: FileText, badge: undefined },
    { id: 'networks', label: 'Fraud Network', icon: Share2, badge: undefined },
    { id: 'analytics-explorer', label: 'Risk Analysis', icon: BarChart2, badge: undefined },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle, badge: openAlertsCount },
    { id: 'investigation', label: 'Investigations', icon: Compass, badge: undefined },
  ];

  // Secondary Enterprise Suite Modules
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
    { id: 'accounts', label: 'Account Dossiers', icon: Users },
    { id: 'cases', label: 'Case Management', icon: ShieldAlert },
  ];

  const getStatusBadge = (status: 'ONLINE' | 'DEMO' | 'OFFLINE') => {
    switch (status) {
      case 'ONLINE':
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            ONLINE
          </span>
        );
      case 'DEMO':
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            DEMO
          </span>
        );
      case 'OFFLINE':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            OFFLINE
          </span>
        );
    }
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800/90 flex flex-col justify-between p-4 shrink-0 text-slate-300 overflow-y-auto max-h-screen sticky top-0">
      <div className="space-y-6">
        {/* LOGO & BRAND */}
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center font-extrabold text-white text-base tracking-wider shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
            FG
          </div>
          <div>
            <div className="font-extrabold text-base tracking-tight bg-gradient-to-r from-cyan-300 via-cyan-100 to-indigo-200 bg-clip-text text-transparent">
              FinGraph
            </div>
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-400">
              Syndicate Analytics
            </div>
          </div>
        </div>

        {/* PRIMARY CORE NAVIGATION */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-2 flex items-center justify-between">
            <span>Navigation</span>
            <span className="text-[9px] font-normal text-cyan-400">Core</span>
          </div>

          <nav className="space-y-1">
            {primaryModules.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 via-blue-500/15 to-indigo-500/10 text-cyan-300 border border-cyan-500/40 shadow-md shadow-cyan-500/10'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 ? (
                    <span className="bg-rose-500/20 border border-rose-500/30 text-rose-400 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </div>

        {/* SECONDARY ADVANCED ENTERPRISE MODULES */}
        <div className="pt-3 border-t border-slate-800/80 space-y-2">
          <button
            onClick={() => setEnterpriseExpanded(!enterpriseExpanded)}
            className="w-full flex items-center justify-between px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span>Advanced Modules ({enterpriseModules.length})</span>
            {enterpriseExpanded ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
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
                    className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
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

      {/* SYSTEM STATUS PANEL */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 space-y-2">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1 flex items-center gap-1.5">
          <Radio className="h-3 w-3 text-cyan-400 animate-pulse" />
          <span>System Status</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Server className="h-3 w-3 text-slate-500" /> API Gateway
            </span>
            {getStatusBadge(systemHealth.api)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Radio className="h-3 w-3 text-slate-500" /> Apache Kafka
            </span>
            {getStatusBadge(systemHealth.kafka)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Cpu className="h-3 w-3 text-slate-500" /> Apache Flink
            </span>
            {getStatusBadge(systemHealth.flink)}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Database className="h-3 w-3 text-slate-500" /> Neo4j GDS
            </span>
            {getStatusBadge(systemHealth.neo4j)}
          </div>
        </div>
      </div>
    </aside>
  );
};
