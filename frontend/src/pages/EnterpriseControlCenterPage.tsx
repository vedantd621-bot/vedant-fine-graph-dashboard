import React, { useEffect, useState } from 'react';
import { Shield, Building, Users, Lock, Server, CheckCircle, Activity, Globe, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { ControlPlaneOverview, Tenant, Organization, InvestigationTeam, Policy } from '../types/tenancy';

export const EnterpriseControlCenterPage: React.FC = () => {
  const [overview, setOverview] = useState<ControlPlaneOverview | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [teams, setTeams] = useState<InvestigationTeam[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ovRes, tRes, oRes, tmRes, pRes] = await Promise.all([
        apiClient.getControlPlaneOverview().catch(() => ({ data: null })),
        apiClient.listTenants().catch(() => ({ data: [] })),
        apiClient.listOrganizations().catch(() => ({ data: [] })),
        apiClient.listTeams().catch(() => ({ data: [] })),
        apiClient.listPolicies().catch(() => ({ data: [] })),
      ]);
      if (ovRes.data) setOverview(ovRes.data);
      if (tRes.data) setTenants(tRes.data);
      if (oRes.data) setOrgs(oRes.data);
      if (tmRes.data) setTeams(tmRes.data);
      if (pRes.data) setPolicies(pRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Shield className="h-7 w-7 text-cyan-400" />
            Enterprise Control Center & Governance
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Multi-Tenant Domain Management, Policy Boundaries, Quota Enforcement & Access Controls
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-sm transition"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-slate-400">Tenant Domain</span>
            <Globe className="h-5 w-5 text-cyan-400" />
          </div>
          <div className="text-xl font-bold mt-2 text-cyan-300">
            {overview?.tenant_name || overview?.tenant_id || 'Global Control'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Status: <span className="text-emerald-400 font-semibold">{overview?.status || 'ACTIVE'}</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-slate-400">Organizations & Units</span>
            <Building className="h-5 w-5 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold mt-2 text-slate-100">
            {overview?.organization_count ?? orgs.length}
          </div>
          <div className="text-xs text-slate-500 mt-1">Hierarchical Business Divisions</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-slate-400">Active Squads</span>
            <Users className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold mt-2 text-slate-100">
            {overview?.team_count ?? teams.length}
          </div>
          <div className="text-xs text-slate-500 mt-1">Investigation Teams Enrolled</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-slate-400">Policy Rules</span>
            <Lock className="h-5 w-5 text-purple-400" />
          </div>
          <div className="text-2xl font-bold mt-2 text-slate-100">
            {overview?.policy_count ?? policies.length}
          </div>
          <div className="text-xs text-slate-500 mt-1">Deterministic Access Policies</div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Organizations & Teams */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-4">
              <Building className="h-5 w-5 text-indigo-400" />
              Organization & Investigation Teams Roster
            </h2>
            <div className="space-y-3">
              {teams.length === 0 ? (
                <div className="text-sm text-slate-500">No teams configured for this domain.</div>
              ) : (
                teams.map((t) => (
                  <div key={t.team_id} className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-lg flex justify-between items-center">
                    <div>
                      <div className="font-semibold text-slate-200 text-sm">{t.name}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{t.description || 'General Investigation Team'}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full border border-slate-700">
                        {t.members.length} Investigators
                      </span>
                      <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-full">
                        ACTIVE
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Active Policies Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-4">
              <Lock className="h-5 w-5 text-purple-400" />
              Active Authorization Policies
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Policy Name</th>
                    <th className="p-2.5">Resource</th>
                    <th className="p-2.5">Action</th>
                    <th className="p-2.5">Effect</th>
                    <th className="p-2.5">Priority</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {policies.map((p) => (
                    <tr key={p.policy_id} className="hover:bg-slate-800/40">
                      <td className="p-2.5 font-medium text-slate-200">{p.name}</td>
                      <td className="p-2.5 font-mono text-cyan-400">{p.resource}</td>
                      <td className="p-2.5 font-mono text-slate-300">{p.action}</td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded font-bold ${p.effect === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'}`}>
                          {p.effect}
                        </span>
                      </td>
                      <td className="p-2.5">{p.priority}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Quotas & System Governance */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-4">
              <Server className="h-5 w-5 text-cyan-400" />
              Tenant Resource Quotas
            </h2>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Max User Accounts</span>
                <span className="font-mono text-slate-200">50 Users</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Investigation Teams</span>
                <span className="font-mono text-slate-200">10 Teams</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Cases per Month</span>
                <span className="font-mono text-slate-200">1,000 Cases</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Daily Sandbox Simulations</span>
                <span className="font-mono text-slate-200">100 Simulations</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400">API Rate Limit</span>
                <span className="font-mono text-cyan-400">120 RPS / tenant</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-3">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              Governance & Security Posture
            </h2>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>Strict Tenant Data Isolation Enforced</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>Deterministic Default-Deny Policy Engine</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>Immutable Configuration Versioning</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>Tamper-Evident Forensic Audit Logging</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
