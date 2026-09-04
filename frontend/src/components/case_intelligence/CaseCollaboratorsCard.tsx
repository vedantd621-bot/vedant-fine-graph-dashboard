import React, { useState } from 'react';
import { Users, UserPlus, Trash2, Shield, Eye, ShieldCheck } from 'lucide-react';
import { CaseCollaborator, CollaboratorRole } from '../../types';

interface CaseCollaboratorsCardProps {
  caseId: string;
  collaborators: CaseCollaborator[];
  isReadOnly?: boolean;
  onAddCollaborator: (userId: string, username: string, role: CollaboratorRole) => Promise<void>;
  onRemoveCollaborator: (userId: string) => Promise<void>;
}

export const CaseCollaboratorsCard: React.FC<CaseCollaboratorsCardProps> = ({
  collaborators,
  isReadOnly = false,
  onAddCollaborator,
  onRemoveCollaborator,
}) => {
  const [showAdd, setShowAdd] = useState(false);
  const [userId, setUserId] = useState('');
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<CollaboratorRole>('COLLABORATOR');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    try {
      setLoading(true);
      await onAddCollaborator(userId || `usr_${username.toLowerCase()}`, username, role);
      setUsername('');
      setUserId('');
      setShowAdd(false);
    } finally {
      setLoading(false);
    }
  };

  const getRoleBadge = (r: CollaboratorRole) => {
    switch (r) {
      case 'OWNER':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30">
            <ShieldCheck className="h-3 w-3" /> Owner
          </span>
        );
      case 'COLLABORATOR':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Shield className="h-3 w-3" /> Collaborator
          </span>
        );
      case 'WATCHER':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/20 text-slate-400 border border-slate-500/30">
            <Eye className="h-3 w-3" /> Watcher
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Users className="h-4 w-4 text-cyan-400" />
          <span>Investigation Team ({collaborators.length})</span>
        </div>
        {!isReadOnly && (
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 transition-all"
          >
            <UserPlus className="h-3.5 w-3.5" />
            <span>Add Member</span>
          </button>
        )}
      </div>

      {showAdd && !isReadOnly && (
        <form onSubmit={handleSubmit} className="p-3 bg-slate-800/60 rounded-lg space-y-2 text-xs border border-slate-700">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. investigator_2"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as CollaboratorRole)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
              >
                <option value="COLLABORATOR">Collaborator</option>
                <option value="WATCHER">Watcher</option>
                <option value="OWNER">Owner</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
            >
              {loading ? 'Assigning...' : 'Assign'}
            </button>
          </div>
        </form>
      )}

      <div className="divide-y divide-slate-800">
        {collaborators.map((c) => (
          <div key={c.collaborator_id} className="py-2 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-200">{c.username}</span>
              {getRoleBadge(c.role)}
            </div>
            {!isReadOnly && c.role !== 'OWNER' && (
              <button
                onClick={() => onRemoveCollaborator(c.user_id)}
                className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors"
                title="Remove collaborator"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
        {collaborators.length === 0 && (
          <div className="py-2 text-xs text-slate-500">No external collaborators assigned.</div>
        )}
      </div>
    </div>
  );
};
