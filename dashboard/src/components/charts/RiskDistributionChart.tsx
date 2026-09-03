import React from 'react';
import { RiskDistribution } from '../../types';

interface RiskDistributionChartProps {
  distribution: RiskDistribution;
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({ distribution }) => {
  const total = distribution.total || 1;
  const categories = [
    { label: 'Critical Risk (75-100)', count: distribution.critical, color: 'bg-rose-500', barColor: '#f43f5e' },
    { label: 'High Risk (50-74)', count: distribution.high, color: 'bg-amber-500', barColor: '#f59e0b' },
    { label: 'Medium Risk (25-49)', count: distribution.medium, color: 'bg-indigo-500', barColor: '#6366f1' },
    { label: 'Low Risk (0-24)', count: distribution.low, color: 'bg-slate-600', barColor: '#475569' },
  ];

  return (
    <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold tracking-tight text-slate-200">
          Account Population Risk Distribution
        </h3>
        <span className="text-xs text-slate-400">{distribution.total} Total Accounts</span>
      </div>

      {/* Stacked Proportional Bar */}
      <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden flex">
        {categories.map((cat, idx) => {
          const pct = ((cat.count / total) * 100);
          if (pct === 0) return null;
          return (
            <div
              key={idx}
              style={{ width: `${pct}%`, backgroundColor: cat.barColor }}
              className="h-full transition-all duration-500 hover:opacity-80"
              title={`${cat.label}: ${cat.count} (${pct.toFixed(1)}%)`}
            />
          );
        })}
      </div>

      {/* Legend & Counts */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        {categories.map((cat, idx) => (
          <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${cat.color}`}></span>
              <span className="text-xs text-slate-300 font-medium">{cat.label.split(' (')[0]}</span>
            </div>
            <span className="text-xs font-bold text-slate-100">{cat.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
