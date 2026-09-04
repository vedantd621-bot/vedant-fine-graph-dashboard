import React, { useEffect, useState } from 'react';
import { Users, Plus, Shield, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { UserResponse, Role } from '../types';

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>(Role.ANALYST);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await apiClient.listTenantUsers();
      if (res.data) setUsers(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.inviteUser({ username, password, role });
      setUsername('');
      setPassword('');
      loadUsers();
    } catch (e: any) {
      alert(e?.response?.data?.error?.message || 'Failed to invite user');
    }
  };

  const handleToggleActive = async (userId: string, currentActive: boolean) => {
    try {
      await apiClient.updateUserStatus(userId, currentActive ? 'SUSPENDED' : 'ACTIVE');
      loadUsers();
    } catch (e: any) {
      alert('Failed to update status');
    }
  };

  return (
    <div className="space-y-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Users className="h-7 w-7 text-cyan-400" />
            User Identity & Role Access Control
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Tenant User Accounts, Role Entitlements, Team Scopes & Status Toggles
          </p>
        </div>
        <button
          onClick={loadUsers}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-sm transition"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Invite Form */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 className="text-sm font-bold uppercase text-slate-300 mb-3 flex items-center gap-2">
          <Plus className="h-4 w-4 text-cyan-400" />
          Enroll New Team Member
        </h2>
        <form onSubmit={handleInvite} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200"
            required
          />
          <input
            type="password"
            placeholder="Temporary Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200"
            required
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-200"
          >
            <option value="ANALYST">ANALYST</option>
            <option value="INVESTIGATOR">INVESTIGATOR</option>
            <option value="ADMIN">ADMIN</option>
            <option value="PLATFORM_ADMIN">PLATFORM_ADMIN</option>
          </select>
          <button
            type="submit"
            className="bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold px-4 py-2 rounded-lg text-sm transition"
          >
            Enroll User
          </button>
        </form>
      </div>

      {/* Users Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="p-3">User ID</th>
              <th className="p-3">Username</th>
              <th className="p-3">Role</th>
              <th className="p-3">Tenant</th>
              <th className="p-3">Status</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {users.map((u) => (
              <tr key={u.user_id} className="hover:bg-slate-800/40">
                <td className="p-3 font-mono text-cyan-400">{u.user_id}</td>
                <td className="p-3 font-semibold text-slate-200">{u.username}</td>
                <td className="p-3">
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {u.role}
                  </span>
                </td>
                <td className="p-3 text-slate-400">{u.tenant_id || 'tnt_default'}</td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${u.is_active ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'}`}>
                    {u.is_active ? 'ACTIVE' : 'SUSPENDED'}
                  </span>
                </td>
                <td className="p-3">
                  <button
                    onClick={() => handleToggleActive(u.user_id, u.is_active)}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] border border-slate-700"
                  >
                    {u.is_active ? 'Suspend' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
