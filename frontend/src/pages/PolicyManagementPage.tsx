import React, { useEffect, useState } from 'react';
import { Lock, Plus, CheckCircle, XCircle, Play, RefreshCw, Shield } from 'lucide-react';
import { apiClient } from '../api/client';
import { Policy, PolicyEffect, PolicyEvaluationResult } from '../types/tenancy';

export const PolicyManagementPage: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  // Form
  const [name, setName] = useState('');
  const [resource, setResource] = useState('*');
  const [action, setAction] = useState('*');
  const [effect, setEffect] = useState<PolicyEffect>('ALLOW');
  const [priority, setPriority] = useState(100);

  // Tester
  const [testResource, setTestResource] = useState('case');
  const [testAction, setTestAction] = useState('create');
  const [testRole, setTestRole] = useState('INVESTIGATOR');
  const [testResult, setTestResult] = useState<PolicyEvaluationResult | null>(null);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const res = await apiClient.listPolicies();
      if (res.data) setPolicies(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createPolicy({ name, resource, action, effect, priority });
      setName('');
      loadPolicies();
    } catch (e: any) {
      alert(e?.response?.data?.error?.message || 'Failed to create policy');
    }
  };

  const handleTest = async () => {
    try {
      const res = await apiClient.evaluatePolicy({
        user_id: 'usr_test',
        role: testRole,
        tenant_id: 'tnt_default',
        resource_type: testResource,
        resource_id: 'case_001',
        resource_tenant_id: 'tnt_default',
        action: testAction,
      });
      if (res.data) setTestResult(res.data);
    } catch (e: any) {
      alert('Evaluation failed');
    }
  };

  return (
    <div className="space-y-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Lock className="h-7 w-7 text-purple-400" />
            Deterministic Policy Engine & Governance
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Ordered Policy Rules, Granular Actions, Tenant Boundaries & Dry-Run Evaluation
          </p>
        </div>
        <button
          onClick={loadPolicies}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-sm transition"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Policy Form */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
          <h2 className="text-sm font-bold uppercase text-slate-300 flex items-center gap-2">
            <Plus className="h-4 w-4 text-purple-400" />
            Create Access Policy Rule
          </h2>
          <form onSubmit={handleCreate} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Policy Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Allow Lead Investigator Override"
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Resource Type</label>
              <input
                type="text"
                value={resource}
                onChange={(e) => setResource(e.target.value)}
                placeholder="*, alert, case, decision"
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Action</label>
              <input
                type="text"
                value={action}
                onChange={(e) => setAction(e.target.value)}
                placeholder="*, read, create, update, delete"
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Effect</label>
                <select
                  value={effect}
                  onChange={(e) => setEffect(e.target.value as PolicyEffect)}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200"
                >
                  <option value="ALLOW">ALLOW</option>
                  <option value="DENY">DENY</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Priority</label>
                <input
                  type="number"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200"
                />
              </div>
            </div>
            <button
              type="submit"
              className="w-full bg-purple-600 hover:bg-purple-500 text-slate-950 font-bold p-2.5 rounded text-xs transition mt-2"
            >
              Add Policy
            </button>
          </form>
        </div>

        {/* Dry-Run Policy Tester */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
          <h2 className="text-sm font-bold uppercase text-slate-300 flex items-center gap-2">
            <Play className="h-4 w-4 text-emerald-400" />
            Dry-Run Policy Evaluator
          </h2>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Target Resource</label>
              <input
                type="text"
                value={testResource}
                onChange={(e) => setTestResource(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Action</label>
              <input
                type="text"
                value={testAction}
                onChange={(e) => setTestAction(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Simulated User Role</label>
              <select
                value={testRole}
                onChange={(e) => setTestRole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200"
              >
                <option value="PLATFORM_ADMIN">PLATFORM_ADMIN</option>
                <option value="ADMIN">ADMIN</option>
                <option value="INVESTIGATOR">INVESTIGATOR</option>
                <option value="ANALYST">ANALYST</option>
              </select>
            </div>
            <button
              onClick={handleTest}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold p-2.5 rounded text-xs transition mt-2"
            >
              Evaluate Access
            </button>

            {testResult && (
              <div className={`p-3 rounded-lg border mt-3 ${testResult.is_allowed ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
                <div className="font-bold flex items-center gap-2">
                  {testResult.is_allowed ? <CheckCircle className="h-4 w-4 text-emerald-400" /> : <XCircle className="h-4 w-4 text-rose-400" />}
                  <span className={testResult.is_allowed ? 'text-emerald-400' : 'text-rose-400'}>
                    DECISION: {testResult.effect}
                  </span>
                </div>
                <div className="text-slate-300 mt-1">{testResult.reason}</div>
              </div>
            )}
          </div>
        </div>

        {/* Policy Summary */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
          <h2 className="text-sm font-bold uppercase text-slate-300 flex items-center gap-2">
            <Shield className="h-4 w-4 text-cyan-400" />
            Evaluation Guarantees
          </h2>
          <ul className="text-xs space-y-2.5 text-slate-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
              <span><strong>Ordered Priority:</strong> Rules evaluate in strict ascending order (priority 100 before 200).</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
              <span><strong>Default Deny:</strong> Any request not explicitly allowed is rejected automatically.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
              <span><strong>Tenant Isolation:</strong> Cross-tenant requests are intercepted and denied before rules evaluate.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Policy Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="p-3">Policy ID</th>
              <th className="p-3">Name</th>
              <th className="p-3">Resource</th>
              <th className="p-3">Action</th>
              <th className="p-3">Effect</th>
              <th className="p-3">Priority</th>
              <th className="p-3">Scope</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {policies.map((p) => (
              <tr key={p.policy_id} className="hover:bg-slate-800/40">
                <td className="p-3 font-mono text-cyan-400">{p.policy_id}</td>
                <td className="p-3 font-medium text-slate-200">{p.name}</td>
                <td className="p-3 font-mono text-slate-300">{p.resource}</td>
                <td className="p-3 font-mono text-slate-300">{p.action}</td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded font-bold ${p.effect === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'}`}>
                    {p.effect}
                  </span>
                </td>
                <td className="p-3">{p.priority}</td>
                <td className="p-3 text-slate-400">{p.tenant_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
