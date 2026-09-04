import React, { useEffect, useState } from 'react';
import { Globe, Plus, Shield, CheckCircle, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { Tenant, TenantStatus } from '../types/tenancy';

export const TenantManagementPage: React.FC = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');

  const loadTenants = async () => {
    setLoading(true);
    try {
      const res = await apiClient.listTenants();
      if (res.data) setTenants(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) return;
    try {
      await apiClient.createTenant({ name, slug });
      setName('');
      setSlug('');
      loadTenants();
    } catch (e: any) {
      alert(e?.response?.data?.error?.message || 'Failed to create tenant');
    }
  };

  const handleStatus = async (tenantId: string, target: TenantStatus) => {
    try {
      await apiClient.transitionTenantStatus(tenantId, target, 'Administrative transition via UI');
      loadTenants();
    } catch (e: any) {
      alert(e?.response?.data?.error?.message || 'Failed to transition tenant');
    }
  };

  return (
    <div className="space-y-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Globe className="h-7 w-7 text-cyan-400" />
            Tenant Domain Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Enterprise Tenant Provisioning, State Transitions & Quota Boundaries
          </p>
        </div>
        <button
          onClick={loadTenants}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-sm transition"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Provision Form */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 className="text-sm font-bold uppercase text-slate-300 mb-3 flex items-center gap-2">
          <Plus className="h-4 w-4 text-cyan-400" />
          Provision New Enterprise Tenant
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Tenant Name (e.g. Apex Global Bank)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            required
          />
          <input
            type="text"
            placeholder="Slug (e.g. apex-global)"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            required
          />
          <button
            type="submit"
            className="bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold px-4 py-2 rounded-lg text-sm transition"
          >
            Provision Domain
          </button>
        </form>
      </div>

      {/* Tenant Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="p-3">Tenant ID</th>
              <th className="p-3">Organization Name</th>
              <th className="p-3">Slug</th>
              <th className="p-3">Status</th>
              <th className="p-3">Max Users</th>
              <th className="p-3">Max Teams</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {tenants.map((t) => (
              <tr key={t.tenant_id} className="hover:bg-slate-800/40">
                <td className="p-3 font-mono text-cyan-400">{t.tenant_id}</td>
                <td className="p-3 font-semibold text-slate-200">{t.name}</td>
                <td className="p-3 font-mono text-slate-400">{t.slug}</td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                    t.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                    t.status === 'SUSPENDED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                    'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                  }`}>
                    {t.status}
                  </span>
                </td>
                <td className="p-3">{t.quotas.max_users}</td>
                <td className="p-3">{t.quotas.max_teams}</td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    {t.status === 'ACTIVE' && (
                      <button
                        onClick={() => handleStatus(t.tenant_id, 'SUSPENDED')}
                        className="px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 rounded text-[11px]"
                      >
                        Suspend
                      </button>
                    )}
                    {t.status === 'SUSPENDED' && (
                      <button
                        onClick={() => handleStatus(t.tenant_id, 'ACTIVE')}
                        className="px-2 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 rounded text-[11px]"
                      >
                        Reactivate
                      </button>
                    )}
                    {t.status !== 'DISABLED' && (
                      <button
                        onClick={() => handleStatus(t.tenant_id, 'DISABLED')}
                        className="px-2 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 rounded text-[11px]"
                      >
                        Disable
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
