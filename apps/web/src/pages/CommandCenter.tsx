import React from 'react';
import { 
  GitCompare, 
  ArrowRight,
  ShieldAlert,
  Search,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Activity,
  Layers,
  Flame,
  Clock,
  HelpCircle,
  Info,
  Sparkles,
  BarChart3
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { DashboardSummary, ClusterListItem } from '../types';
import { Badge } from '../components/common/Badge';

interface CommandCenterProps {
  summary: DashboardSummary | null;
  clusters: ClusterListItem[];
  onSelectCluster: (clusterId: string) => void;
  onNavigateToComparison: () => void;
  onRunPipeline: () => void;
  isAnalyzing: boolean;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  summary,
  clusters,
  onSelectCluster,
  onNavigateToComparison,
  onRunPipeline,
  isAnalyzing
}) => {
  const hero = summary?.hero_cluster;
  const chartData = hero?.time_series || [];

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto text-slate-900">
      {/* Educational Welcome & Purpose Banner */}
      <div className="p-5 rounded-lg bg-white border border-slate-200/80 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Live Surveillance
            </span>
            <h1 className="text-lg font-bold text-slate-900 tracking-tight font-sans">
              Reliability Engineering Command Center
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            WarrantyPatternMiner continuously analyzes unstructured technician diagnostic narratives to uncover hidden cross-code failure patterns before they escalate into high-cost field recalls.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={onNavigateToComparison}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-sm transition-all"
          >
            <GitCompare className="h-4 w-4 text-blue-600" />
            <span>Why Traditional Alarms Failed</span>
          </button>
        </div>
      </div>

      {/* 4 Core Executive Metric Cards with Plain-English Explanations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Claims Ingested */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between space-y-3 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 font-sans">Claims Ingested</span>
            <div className="p-1.5 rounded bg-blue-50 text-blue-600">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-slate-900">
              {summary ? summary.claims_analyzed.toLocaleString() : '—'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-snug">
              Total raw warranty claim records normalized & embedded into semantic vector space.
            </p>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-blue-600 h-full rounded-full" style={{ width: summary && summary.claims_analyzed > 0 ? '100%' : '0%' }}></div>
          </div>
        </div>

        {/* Metric 2: Discovered Clusters */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between space-y-3 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 font-sans">Discovered Defect Patterns</span>
            <div className="p-1.5 rounded bg-indigo-50 text-indigo-600">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-slate-900">
              {summary ? summary.emerging_patterns : '—'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-snug">
              Unsupervised HDBSCAN clusters grouped by true physical symptom similarity.
            </p>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-600 h-full rounded-full" style={{ width: summary && summary.emerging_patterns > 0 ? '85%' : '0%' }}></div>
          </div>
        </div>

        {/* Metric 3: Active Anomalies */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between space-y-3 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 font-sans">Active Critical Surges</span>
            <div className="p-1.5 rounded bg-red-50 text-red-600">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <div>
            <div className={`text-2xl font-bold font-mono ${summary && summary.high_risk_patterns > 0 ? 'text-red-700' : 'text-slate-900'}`}>
              {summary ? summary.high_risk_patterns : '—'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-snug">
              Defect clusters with statistical growth exceeding the composite alert threshold (&ge;80).
            </p>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-red-600 h-full rounded-full" style={{ width: summary && summary.high_risk_patterns > 0 ? '100%' : '0%' }}></div>
          </div>
        </div>

        {/* Metric 4: Code Mismatches */}
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between space-y-3 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 font-sans">Taxonomy Mismatches</span>
            <div className="p-1.5 rounded bg-amber-50 text-amber-600">
              <Flame className="h-4 w-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-amber-700">
              {summary ? summary.miscoded_claims : '—'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-snug">
              Claims where the assigned checkbox code contradicted the technician's actual notes.
            </p>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: summary && summary.miscoded_claims > 0 ? '60%' : '0%' }}></div>
          </div>
        </div>
      </div>

      {/* Dominant Active Anomaly Spotlight */}
      {hero ? (
        <div className="p-6 rounded-lg bg-white border border-slate-200 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded text-xs font-bold font-mono uppercase bg-red-100 text-red-800 border border-red-200 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
                Top Priority Anomaly Requiring Engineering Attention
              </span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Cluster Ref: <strong className="text-slate-800">{hero.id.slice(0, 8)}</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Defect Information & Story */}
            <div className="lg:col-span-7 space-y-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900 font-sans tracking-tight">
                  {hero.label}
                </h2>
                <p className="text-xs text-slate-600 leading-relaxed mt-1.5">
                  {hero.description}
                </p>
              </div>

              {/* 3 Key Numerical Indicators */}
              <div className="grid grid-cols-3 gap-3 p-4 rounded-lg bg-slate-50 border border-slate-200/80 font-mono">
                <div>
                  <span className="text-[11px] text-slate-500 uppercase font-sans font-semibold block">Composite Score</span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className="text-2xl font-bold text-slate-900">{hero.alert_score}</span>
                    <span className="text-xs text-slate-500 font-normal">/ 100</span>
                  </div>
                  <span className="text-[10px] text-red-700 font-bold uppercase block mt-0.5">Critical Alert</span>
                </div>

                <div>
                  <span className="text-[11px] text-slate-500 uppercase font-sans font-semibold block">Surge Velocity</span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className="text-2xl font-bold text-red-700">+{hero.growth_rate}%</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mt-0.5">vs 6-mo baseline</span>
                </div>

                <div>
                  <span className="text-[11px] text-slate-500 uppercase font-sans font-semibold block">Consolidated Total</span>
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className="text-2xl font-bold text-blue-700">{hero.claim_count}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mt-0.5">related claims</span>
                </div>
              </div>

              <div>
                <button
                  onClick={() => onSelectCluster(hero.id)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-md text-xs font-bold font-sans bg-slate-900 hover:bg-slate-800 text-white transition-all shadow-sm"
                >
                  <span>Open Deep Investigation Workstation</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Right: Why This Was Hidden from Legacy Tools */}
            <div className="lg:col-span-5 p-4 rounded-lg bg-blue-50/50 border border-blue-100 space-y-4 text-xs font-sans">
              <div className="flex items-center gap-2 text-blue-900 font-bold">
                <Info className="h-4 w-4 text-blue-600 shrink-0" />
                <span>Why Legacy Single-Code Monitors Missed This Defect</span>
              </div>

              {/* Volume vs Baseline Comparison Bar */}
              <div className="space-y-2 font-mono">
                <div>
                  <div className="flex justify-between text-xs text-slate-700 mb-1">
                    <span>July Surge Volume</span>
                    <span className="font-bold text-red-700">17 claims / mo</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-red-600 h-full rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Historical Monthly Baseline</span>
                    <span>3.0 claims / mo</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-slate-400 h-full rounded-full" style={{ width: '18%' }}></div>
                  </div>
                </div>
              </div>

              {/* Taxonomy Fragmentation Explanation */}
              <div className="p-3 rounded bg-white border border-blue-200/60 text-slate-700 space-y-1 leading-relaxed">
                <span className="font-bold text-slate-900 block text-[11px] uppercase tracking-wide">
                  Taxonomy Fragmentation:
                </span>
                <p className="text-xs">
                  These 35 claims were fragmented across <strong className="text-slate-900">5 different dealership failure codes</strong> (OTHER: 10, RIDE QUALITY: 8, SUSPENSION: 7, STEERING: 5, ELECTRICAL: 5). Because no single code exceeded 10 claims, legacy systems stayed silent while semantic clustering flagged the surge.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-8 text-center bg-white rounded-lg border border-slate-200 shadow-sm">
          <CheckCircle2 className="h-8 w-8 text-slate-400 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-900 font-sans">No Critical Defect Anomalies</h3>
          <p className="text-xs text-slate-500 mt-1">All monitored vehicle subsystems are operating within historical baseline parameters.</p>
        </div>
      )}

      {/* Signal Emergence Timeline Chart */}
      {chartData.length > 0 && (
        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                Signal Emergence Timeline (Observed Claims vs Historical Baseline)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Shows the monthly progression of the primary defect cluster over the 7-month observation horizon.
              </p>
            </div>
            <div className="flex items-center gap-4 font-mono text-xs">
              <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
                <span className="w-3 h-1.5 bg-blue-600 rounded-sm inline-block"></span>
                Observed Volume
              </span>
              <span className="flex items-center gap-1.5 text-slate-500">
                <span className="w-3 h-0.5 bg-slate-400 stroke-dashed inline-block"></span>
                Rolling Baseline
              </span>
              <span className="flex items-center gap-1.5 text-red-600 font-semibold">
                <span className="w-3 h-0.5 bg-red-500 inline-block"></span>
                Legacy Threshold (10)
              </span>
            </div>
          </div>

          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="claimGradientLight" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="period" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }} />
                <YAxis stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '6px', color: '#0f172a', fontSize: '12px', fontFamily: 'monospace', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)' }} 
                />
                <Area type="monotone" dataKey="claim_count" name="Observed Claims" stroke="#2563eb" strokeWidth={2.5} fill="url(#claimGradientLight)" />
                <Area type="monotone" dataKey="baseline" name="Baseline Mean" stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1.5} fill="none" />
                <ReferenceLine y={10} label={{ value: 'Traditional Code Threshold (10)', fill: '#dc2626', fontSize: 11, position: 'insideTopRight' }} stroke="#dc2626" strokeDasharray="3 3" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Discovered Defect Patterns Table */}
      <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 font-sans">
              All Discovered Defect Patterns ({clusters.length})
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Click on any row to open the complete investigation workstation with verbatim narratives and statistical proof.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-mono border-b border-slate-200 tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Pattern / Diagnostic Scope</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3 text-right">Score</th>
                <th className="py-2.5 px-3 text-right">Volume</th>
                <th className="py-2.5 px-3 text-right">Surge vs Baseline</th>
                <th className="py-2.5 px-3 text-right">Codes</th>
                <th className="py-2.5 px-3 text-right">Plants</th>
                <th className="py-2.5 px-3">Review Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {clusters.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 font-sans text-xs">
                    No defect patterns detected in current dataset.
                  </td>
                </tr>
              ) : (
                clusters.map((c) => (
                  <tr 
                    key={c.id} 
                    onClick={() => onSelectCluster(c.id)}
                    className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-sans font-semibold text-slate-900">
                      {c.label}
                    </td>
                    <td className="py-3 px-3">
                      <Badge level={c.alert_level} size="sm">
                        {c.alert_level}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-slate-900">
                      {c.alert_score}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-700">
                      {c.claim_count}
                    </td>
                    <td className={`py-3 px-3 text-right font-bold ${c.growth_rate > 0 ? 'text-red-700' : 'text-slate-500'}`}>
                      +{c.growth_rate}%
                    </td>
                    <td className="py-3 px-3 text-right text-slate-500">
                      {c.cross_code_count}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-500">
                      {c.plant_count}
                    </td>
                    <td className="py-3 px-3 font-sans">
                      <span className={`text-[10px] font-mono uppercase font-bold ${
                        c.status === 'confirmed' ? 'text-emerald-700' :
                        c.status === 'dismissed' ? 'text-slate-400 line-through' :
                        'text-slate-500'
                      }`}>
                        {c.status || 'unreviewed'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCluster(c.id);
                        }}
                        className="text-xs font-sans text-blue-600 hover:text-blue-800 font-bold"
                      >
                        Investigate &rarr;
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
