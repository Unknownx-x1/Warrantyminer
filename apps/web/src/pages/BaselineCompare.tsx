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
  Sparkles
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
            Dealership technicians assigned 5 different failure codes (OTHER, RIDE QUALITY, SUSPENSION, STEERING, ELECTRICAL-NFF) to the same physical suspension knocking noise.
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
            WarrantyPatternMiner reads verbatim complaint narratives, groups the 35 claims by physical meaning, and exposes the +466.7% surge 69 days before traditional systems notice.
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
                <span className="text-[10px] text-slate-500 mt-0.5 block">5-Factor Model</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
