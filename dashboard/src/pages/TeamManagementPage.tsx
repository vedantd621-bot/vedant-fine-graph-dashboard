import React, { useEffect, useState } from 'react';
import { Users, Plus, Shield, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { InvestigationTeam, Organization } from '../types/tenancy';

export const TeamManagementPage: React.FC = () => {
  const [teams, setTeams] = useState<InvestigationTeam[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [orgId, setOrgId] = useState('org_default');

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, oRes] = await Promise.all([
        apiClient.listTeams(),
        apiClient.listOrganizations().catch(() => ({ data: [] })),
      ]);
      if (tRes.data) setTeams(tRes.data);
      if (oRes.data) setOrgs(oRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createTeam({ org_id: orgId, name, description });
      setName('');
      setDescription('');
      loadData();
    } catch (e: any) {
      alert(e?.response?.data?.error?.message || 'Failed to create team');
    }
  };

  return (
    <div className="space-y-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Users className="h-7 w-7 text-indigo-400" />
            Investigation Team Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Investigation Squads, Team Leads, Member Assignment & Scoped Work Queues
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

      {/* Create Team Form */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 className="text-sm font-bold uppercase text-slate-300 mb-3 flex items-center gap-2">
          <Plus className="h-4 w-4 text-indigo-400" />
          Create Investigation Team
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Team Name (e.g. Cyber Mule Squad)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200"
            required
          />
          <input
            type="text"
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200"
          />
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-lg text-sm transition"
          >
            Create Team
          </button>
        </form>
      </div>

      {/* Teams Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {teams.map((t) => (
          <div key={t.team_id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-slate-100 text-base">{t.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{t.description || 'General Investigation Unit'}</p>
              </div>
              <span className="text-xs font-mono bg-slate-800 text-cyan-400 px-2 py-0.5 rounded border border-slate-700">
                {t.team_id}
              </span>
            </div>

            <div>
              <div className="text-xs font-bold uppercase text-slate-400 mb-2">Team Members ({t.members.length})</div>
              <div className="space-y-1.5">
                {t.members.length === 0 ? (
                  <div className="text-xs text-slate-500 italic">No assigned members</div>
                ) : (
                  t.members.map((m) => (
                    <div key={m.user_id} className="flex justify-between items-center text-xs p-2 bg-slate-950/60 rounded border border-slate-800/80">
                      <span className="font-medium text-slate-200">{m.username}</span>
                      <span className="text-[11px] bg-slate-800 text-indigo-300 px-2 py-0.5 rounded">{m.role}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
