import React from 'react';
import { 
  Activity, 
  Search, 
  Layers, 
  GitCompare, 
  Cpu, 
  Database, 
  Play,
  ShieldCheck
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onRunPipeline: () => void;
  isAnalyzing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onRunPipeline,
  isAnalyzing
}) => {
  const navItems = [
    { id: 'command-center', label: 'Command Center', icon: Activity },
    { id: 'investigation', label: 'Investigation Console', icon: Layers },
    { id: 'comparison', label: 'Baseline Reveal', icon: GitCompare },
    { id: 'claims', label: 'Claims Explorer', icon: Search },
    { id: 'fingerprints', label: 'Defect Memory', icon: Cpu },
    { id: 'pipeline', label: 'Pipeline & Data', icon: Database }
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo & Product Identity */}
          <div className="flex items-center gap-3">
            <div className="h-7 w-7 rounded-[4px] bg-slate-900 flex items-center justify-center text-white shadow-xs">
              <ShieldCheck className="h-4 w-4 text-white" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-bold text-sm tracking-tight text-slate-900 font-sans">
                WarrantyPatternMiner
              </span>
              <span className="text-[10px] text-blue-700 font-mono tracking-wider font-semibold hidden sm:inline px-1.5 py-0.5 rounded-[3px] bg-blue-50 border border-blue-200">
                RELIABILITY INTELLIGENCE
              </span>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 text-xs transition-all rounded-[3px] ${
                    isActive
                      ? 'text-blue-700 font-semibold bg-blue-50/80 border border-blue-200/80 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 border border-transparent'
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span className="hidden md:inline font-sans">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Primary Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={onRunPipeline}
              disabled={isAnalyzing}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-[3px] text-xs font-semibold font-mono uppercase tracking-wider transition-all shadow-xs ${
                isAnalyzing
                  ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                  : 'bg-slate-900 hover:bg-slate-800 text-white border border-slate-800 active:scale-[0.98]'
              }`}
            >
              <Play className={`h-3 w-3 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>{isAnalyzing ? 'Executing...' : 'Run Pipeline'}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
