import React from 'react';

interface BadgeProps {
  level?: 'CRITICAL' | 'HIGH' | 'WATCH' | 'NORMAL' | string;
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ level = 'NORMAL', children, className = '', size = 'md' }) => {
  const upper = String(level).toUpperCase();
  
  let colorStyle = 'bg-slate-100 text-slate-700 border-slate-200';
  let dotColor = 'bg-slate-400';

  if (upper === 'CRITICAL') {
    colorStyle = 'bg-red-50 text-red-700 border-red-200 font-bold';
    dotColor = 'bg-red-600';
  } else if (upper === 'HIGH') {
    colorStyle = 'bg-orange-50 text-orange-700 border-orange-200 font-bold';
    dotColor = 'bg-orange-500';
  } else if (upper === 'WATCH') {
    colorStyle = 'bg-amber-50 text-amber-800 border-amber-200 font-semibold';
    dotColor = 'bg-amber-500';
  } else if (upper === 'NORMAL' || upper === 'CONFIRMED') {
    colorStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold';
    dotColor = 'bg-emerald-600';
  } else if (upper === 'DISMISSED') {
    colorStyle = 'bg-slate-100 text-slate-400 border-slate-200 line-through';
    dotColor = 'bg-slate-400';
  } else if (upper === 'UNREVIEWED') {
    colorStyle = 'bg-slate-100 text-slate-600 border-slate-200';
    dotColor = 'bg-slate-400';
  }

  const sizeStyle = size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-[3px] border font-mono tracking-tight ${sizeStyle} ${colorStyle} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />
      {children}
    </span>
  );
};
