import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ArrowLeft,
  DollarSign,
  Activity,
  CheckCircle,
  Clock,
  Layers,
  Info,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Campaign, CampaignRiskExplanation, InvestigationCaseSummary } from '../types';

interface FraudCampaignDetailPageProps {
  campaignId: string;
  onBack: () => void;
  onSelectCase?: (caseId: string) => void;
}

export const FraudCampaignDetailPage: React.FC<FraudCampaignDetailPageProps> = ({
  campaignId,
  onBack,
  onSelectCase,
}) => {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [explanation, setExplanation] = useState<CampaignRiskExplanation | null>(null);
  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [campRes, expRes, casesRes] = await Promise.all([
        apiClient.getCampaign(campaignId),
        apiClient.getCampaignExplanation(campaignId).catch(() => ({ data: null })),
        apiClient.getCampaignCases(campaignId).catch(() => ({ data: [] })),
      ]);
      setCampaign(campRes.data);
      setExplanation(expRes.data);
      setCases(casesRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campaignId]);

  if (loading) {
    return <div className="p-12 text-center text-xs text-slate-400">Loading campaign dossier...</div>;
  }

  if (!campaign) {
    return <div className="p-6 text-rose-400">Campaign not found.</div>;
  }

  return (
    <div className="space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        <span>Back to Command Center</span>
      </button>

      {/* Campaign Header */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <ShieldAlert className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100">{campaign.name}</h1>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {campaign.status}
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{campaign.description}</p>
      </div>

      {/* Exposure Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-xs text-slate-400">Financial Exposure</div>
          <div className="text-2xl font-bold text-amber-400">${campaign.financial_exposure.toLocaleString()}</div>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-xs text-slate-400">Confirmed Fraud Value</div>
          <div className="text-2xl font-bold text-rose-400">${campaign.confirmed_fraud_value.toLocaleString()}</div>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-xs text-slate-400">Campaign Risk Score</div>
          <div className="text-2xl font-bold text-purple-400">{campaign.risk_score} / 100</div>
        </div>
      </div>

      {/* 6-Factor Risk Breakdown */}
      {explanation && (
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Deterministic 6-Factor Risk Formulation
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {explanation.factors.map((f, i) => (
              <div key={i} className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">{f.factor_name}</span>
                  <span className="font-bold text-cyan-400">{f.contribution} pts</span>
                </div>
                <div className="text-[11px] text-slate-400">{f.evidence}</div>
                <div className="text-[10px] text-slate-500">Weight: {Math.round(f.weight * 100)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Associated Cases */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Clustered Investigation Cases ({cases.length})
        </span>
        <div className="divide-y divide-slate-800 text-xs">
          {cases.map((c) => (
            <div
              key={c.case_id}
              onClick={() => onSelectCase && onSelectCase(c.case_id)}
              className="py-3 flex items-center justify-between hover:bg-slate-800/40 px-2 rounded cursor-pointer transition-colors"
            >
              <div>
                <span className="font-semibold text-slate-200">{c.case_id} — {c.title}</span>
                <div className="text-[11px] text-slate-400">{c.accounts_count} Accounts • {c.alerts_count} Alerts</div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {c.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
