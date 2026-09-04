import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  trendPositive?: boolean;
  icon?: React.ReactNode;
  alertColor?: 'critical' | 'high' | 'normal' | 'sky';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendPositive = true,
  icon,
  alertColor = 'sky'
}) => {
  let borderAccent = 'border-slate-800 hover:border-slate-700';
  let valueColor = 'text-white';
  
  if (alertColor === 'critical') {
    borderAccent = 'border-red-900/40 hover:border-red-800/80 bg-gradient-to-b from-red-950/20 to-slate-900/50';
    valueColor = 'text-red-400';
  } else if (alertColor === 'high') {
    borderAccent = 'border-orange-900/40 hover:border-orange-800/80 bg-gradient-to-b from-orange-950/20 to-slate-900/50';
    valueColor = 'text-orange-400';
  } else {
    borderAccent = 'border-slate-800 hover:border-sky-800/50 bg-[#111827]/70';
  }

  return (
    <div className={`p-5 rounded-xl border transition-all shadow-sm ${borderAccent}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">{title}</span>
        {icon && <div className="text-slate-400 p-2 rounded-lg bg-slate-800/60">{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-3xl font-bold tracking-tight font-mono ${valueColor}`}>{value}</span>
        {trend && (
          <span className={`text-xs font-semibold font-mono ${trendPositive ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
};
