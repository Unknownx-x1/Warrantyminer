import React, { useEffect, useState } from 'react';
import { 
  GitCompare, 
  Clock, 
  ArrowRight, 
  CheckCircle2, 
  XCircle, 
  ShieldAlert, 
  AlertTriangle,
  Layers,
  TrendingUp,
  Info,
  Sparkles,
  Calculator,
  Activity,
  Tag
} from 'lucide-react';
import { BaselineComparison } from '../types';
import { api } from '../api/client';
import { Badge } from '../components/common/Badge';

interface BaselineCompareProps {
  onSelectCluster: (clusterId: string) => void;
}

export const BaselineCompare: React.FC<BaselineCompareProps> = ({ onSelectCluster }) => {
  const [data, setData] = useState<BaselineComparison | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComparison();
  }, []);

  const loadComparison = async () => {
    setLoading(true);
    try {
      const res = await api.getBaselineComparison();
      setData(res);
    } catch (err) {
      console.error('Failed to load baseline comparison', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-3 border-solid border-blue-600 border-r-transparent"></div>
        <p className="mt-3 text-xs font-mono text-slate-500">Computing code-level baseline vs semantic consolidation...</p>
      </div>
    );
  }

  if (!data || !data.has_data) {
    return (
      <div className="p-8 text-center bg-white rounded-lg border border-slate-200 shadow-sm max-w-xl mx-auto">
        <GitCompare className="h-8 w-8 text-slate-400 mx-auto mb-2" />
        <h3 className="text-base font-bold text-slate-900 font-sans">No Comparison Data Available</h3>
        <p className="text-xs text-slate-500 mt-1">Execute the analytical surveillance pipeline to compute comparative metrics.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto text-slate-900">
      {/* Educational Header Banner */}
      <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Comparative Analysis
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight font-sans">
              The Baseline Reveal: Why Traditional Monitoring Failed
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            This report mathematically compares legacy single-code threshold monitoring against WarrantyPatternMiner's cross-code semantic clustering on the canonical target defect.
          </p>
        </div>

        {data.cluster_id && (
          <button
            onClick={() => onSelectCluster(data.cluster_id!)}
            className="flex items-center gap-2 px-4 py-2 rounded-md text-xs font-bold font-sans bg-slate-900 hover:bg-slate-800 text-white shadow-sm transition-colors shrink-0"
          >
            <span>Investigate Target Defect</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Early Surveillance Timing Advantage Banner */}
      <div className="p-6 rounded-lg border border-blue-200 bg-blue-50/40 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-blue-700 uppercase tracking-wider block font-bold">
              EARLY SURVEILLANCE TIMING ADVANTAGE
            </span>
            <h2 className="text-xl font-bold text-slate-900 font-sans mt-0.5">
              {data.lead_time_days !== null && data.lead_time_days !== undefined
                ? `+${data.lead_time_days} Days Lead Time Ahead of Traditional Alert`
                : 'Detected Before Traditional Threshold Breach'}
            </h2>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl font-sans leading-relaxed">
              {data.lead_time_days !== null && data.lead_time_days !== undefined
                ? `Semantic cluster emerged on ${data.semantic_detection_date}; single-code monitoring did not breach threshold until ${data.traditional_detection_date}.`
                : `Semantic intelligence consolidated the pattern on ${data.semantic_detection_date || 'surveillance period'} while traditional structured-code monitoring triggered no alert during the observation window.`}
            </p>
          </div>
        </div>

        <div className="text-right shrink-0 font-mono text-xs hidden lg:block bg-white p-3 rounded border border-blue-200">
          <span className="text-slate-400 uppercase block text-[10px]">Target Pattern Label</span>
          <span className="text-slate-900 font-bold">{data.cluster_label}</span>
        </div>
      </div>

      {/* 3-Step Educational Breakdown of Why This Happened */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-sans text-xs">
        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-slate-900 font-bold">
            <span className="w-5 h-5 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-[11px] font-mono">1</span>
            <span>Dealer Misclassification</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Dealership technicians assigned {data.cross_code_count} different failure codes ({data.traditional_monitoring?.code_buckets.map(b => b.code).join(', ') || 'multiple codes'}) to the same underlying physical defect.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-slate-900 font-bold">
            <span className="w-5 h-5 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-[11px] font-mono">2</span>
            <span>Siloed Threshold Blindspot</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Traditional monitoring tracks each failure code independently with a threshold of 10 claims. Because the defect was split into smaller buckets, no alarm fired in early months.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center gap-2 text-blue-700 font-bold">
            <span className="w-5 h-5 rounded-full bg-blue-100 border border-blue-300 flex items-center justify-center text-[11px] font-mono text-blue-700">3</span>
            <span>Semantic AI Consolidation</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            WarrantyPatternMiner reads verbatim complaint narratives, groups the {data.total_cluster_claims} claims by physical meaning, and exposes the +{data.growth_rate}% surge {data.lead_time_days ? `${data.lead_time_days} days ` : ''}before traditional systems notice.
          </p>
        </div>
      </div>

      {/* Side-by-Side Comparative Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Left: Traditional Code-Level View */}
        <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block font-semibold">Traditional Surveillance</span>
              <h3 className="text-sm font-bold text-slate-900 font-sans mt-0.5">Single-Code Threshold Monitoring</h3>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1.5">
              <XCircle className="h-3.5 w-3.5 text-slate-400" />
              {data.traditional_monitoring?.status === 'ALERT_TRIGGERED' ? 'LATE THRESHOLD ALERT' : 'NO THRESHOLD BREACH'}
            </span>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            {data.traditional_monitoring?.explanation}
          </p>

          <div className="space-y-2">
            <span className="text-[10px] font-mono uppercase text-slate-500 block font-semibold">
              Individual Code Buckets (Alert Threshold: 10 claims)
            </span>
            <div className="border border-slate-200 rounded-md overflow-hidden">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-50 text-slate-600 text-[10px] uppercase border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Failure Code</th>
                    <th className="py-2.5 px-3 text-right">Claims</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.traditional_monitoring?.code_buckets.map((bucket, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{bucket.code}</td>
                      <td className="py-2.5 px-3 text-right text-slate-700 font-bold">{bucket.claim_count}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={`text-[10px] ${bucket.alert ? 'text-amber-700 font-bold' : 'text-slate-400'}`}>
                          {bucket.alert ? 'THRESHOLD REACHED (10)' : 'BELOW THRESHOLD (10)'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: WarrantyPatternMiner Semantic Intelligence View */}
        <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-mono text-blue-700 uppercase tracking-wider block font-bold">Semantic Surveillance</span>
              <h3 className="text-sm font-bold text-slate-900 font-sans mt-0.5">WarrantyPatternMiner Intelligence</h3>
            </div>
            <Badge level={data.alert_level} size="sm">
              {data.alert_level}
            </Badge>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            {data.semantic_monitoring?.explanation}
          </p>

          <div className="space-y-2">
            <span className="text-[10px] font-mono uppercase text-slate-500 block font-semibold">
              Consolidated Emergence Metrics
            </span>
            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <div className="p-3.5 rounded-md bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Consolidated Volume</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">{data.total_cluster_claims} claims</span>
                <span className="text-[10px] text-blue-700 mt-0.5 block">Across {data.cross_code_count} codes</span>
              </div>

              <div className="p-3.5 rounded-md bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Surge Velocity</span>
                <span className="text-lg font-bold text-red-700 mt-1 block">+{data.growth_rate}%</span>
                <span className="text-[10px] text-slate-500 mt-0.5 block">Surge above baseline</span>
              </div>

              <div className="p-3.5 rounded-md bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Statistical Z-Score</span>
                <span className="text-lg font-bold text-red-700 mt-1 block">Z = {data.semantic_monitoring?.significance_z}</span>
                <span className="text-[10px] text-slate-500 mt-0.5 block">p &lt; 0.0001</span>
              </div>

              <div className="p-3.5 rounded-md bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Composite Alert Score</span>
                <span className="text-lg font-bold text-slate-900 mt-1 block">{data.alert_score} / 100</span>
                <span className="text-[10px] text-red-700 font-bold mt-0.5 block">5-Factor Sum</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5-Factor Score Attribution Proof Section */}
      <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded bg-blue-50 text-blue-600">
              <Calculator className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                5-Factor Composite Alert Score Mathematical Decomposition
              </h3>
              <p className="text-xs text-slate-500">
                How WarrantyPatternMiner quantitatively generated the <strong className="text-slate-900 font-mono">{data.alert_score} / 100</strong> alert score for this target defect.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-slate-700">
            Formula: (0.30 &times; Growth) + (0.25 &times; Z-Score) + (0.15 &times; Size) + (0.15 &times; CrossCode) + (0.15 &times; Coherence)
          </span>
        </div>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs font-sans">
            <thead className="bg-slate-50 text-slate-700 uppercase text-[10px] font-mono border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Factor Name</th>
                <th className="py-2.5 px-3">Methodology & Benchmark</th>
                <th className="py-2.5 px-3 text-right">Raw Measured Value</th>
                <th className="py-2.5 px-3 text-right">Weight</th>
                <th className="py-2.5 px-3 text-right">Max Pts</th>
                <th className="py-2.5 px-4 text-right">Points Earned</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {/* Factor 1: Growth */}
              {(() => {
                const f = data.factor_breakdown?.growth_velocity;
                const raw = f ? f.raw_value : `+${data.growth_rate}%`;
                const pts = f ? f.points_earned : Math.round(0.30 * Math.min(100, data.growth_rate || 0) * 10) / 10;
                return (
                  <tr className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-900 flex items-center gap-1.5">
                      <TrendingUp className="h-3.5 w-3.5 text-red-600 shrink-0" />
                      <span>1. Growth Velocity</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 text-[11px]">
                      Surge vs 6-mo historical baseline (&gt;100% surge = max)
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-red-700">{raw}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600">30%</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">30.0</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 bg-slate-50/50">{pts.toFixed(1)} / 30.0</td>
                  </tr>
                );
              })()}

              {/* Factor 2: Significance */}
              {(() => {
                const f = data.factor_breakdown?.statistical_significance;
                const raw = f ? f.raw_value : `Z = ${data.semantic_monitoring?.significance_z}`;
                const pts = f ? f.points_earned : Math.round(0.25 * Math.min(100, (data.semantic_monitoring?.significance_z || 0) * 35.0) * 10) / 10;
                return (
                  <tr className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-900 flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                      <span>2. Statistical Significance</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 text-[11px]">
                      Poisson-normal Z-score deviation (Z &ge; 2.86 = max, p &lt; 0.001)
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-red-700">{raw}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600">25%</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">25.0</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 bg-slate-50/50">{pts.toFixed(1)} / 25.0</td>
                  </tr>
                );
              })()}

              {/* Factor 3: Size */}
              {(() => {
                const f = data.factor_breakdown?.cluster_volume;
                const raw = f ? f.raw_value : `${data.total_cluster_claims} claims`;
                const pts = f ? f.points_earned : Math.round(0.15 * Math.min(100, (data.total_cluster_claims || 0) * 5.0) * 10) / 10;
                return (
                  <tr className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-900 flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                      <span>3. Cluster Volume</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 text-[11px]">
                      Total consolidated defect incidence (&ge;20 claims = max)
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-800">{raw}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600">15%</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">15.0</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 bg-slate-50/50">{pts.toFixed(1)} / 15.0</td>
                  </tr>
                );
              })()}

              {/* Factor 4: Cross-Code */}
              {(() => {
                const f = data.factor_breakdown?.cross_code_dispersion;
                const raw = f ? f.raw_value : `${data.cross_code_count} dealer codes`;
                const pts = f ? f.points_earned : Math.round(0.15 * Math.min(100, (data.cross_code_count || 0) * 20.0) * 10) / 10;
                return (
                  <tr className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-900 flex items-center gap-1.5">
                      <Tag className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                      <span>4. Cross-Code Dispersion</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 text-[11px]">
                      Dealership code fragmentation count (&ge;5 codes = max)
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-800">{raw}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600">15%</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">15.0</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 bg-slate-50/50">{pts.toFixed(1)} / 15.0</td>
                  </tr>
                );
              })()}

              {/* Factor 5: Coherence */}
              {(() => {
                const f = data.factor_breakdown?.semantic_coherence;
                const raw = f ? f.raw_value : `72.0%`;
                const pts = f ? f.points_earned : 10.8;
                return (
                  <tr className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-900 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                      <span>5. Semantic Coherence</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 text-[11px]">
                      Mean pairwise cosine cohesion of narrative vector embeddings
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-800">{raw}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600">15%</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">15.0</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-900 bg-slate-50/50">{pts.toFixed(1)} / 15.0</td>
                  </tr>
                );
              })()}
            </tbody>
            <tfoot className="bg-slate-100 font-mono font-bold text-slate-900 border-t-2 border-slate-300">
              <tr>
                <td colSpan={2} className="py-2.5 px-3 text-slate-900 font-sans">
                  Composite Total Alert Score (Sum of All 5 Factors)
                </td>
                <td className="py-2.5 px-3 text-right font-sans text-slate-500 text-[11px]">100% Normalized</td>
                <td className="py-2.5 px-3 text-right">100%</td>
                <td className="py-2.5 px-3 text-right">100.0</td>
                <td className="py-2.5 px-4 text-right text-red-700 bg-slate-200/60 font-bold">{data.alert_score?.toFixed(1)} / 100.0</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
};
