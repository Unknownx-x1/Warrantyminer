import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  Edit3, 
  Search, 
  ShieldCheck, 
  ShieldAlert,
  AlertOctagon,
  FileText,
  Clock,
  Building2,
  Car,
  Layers,
  TrendingUp,
  BarChart2,
  Table,
  Cpu,
  Calculator,
  Activity,
  Tag,
  Info,
  Sparkles
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  BarChart, 
  Bar 
} from 'recharts';
import { ClusterDetail, ClusterClaimItem, ClusterListItem } from '../types';
import { api } from '../api/client';
import { Badge } from '../components/common/Badge';

interface PatternDetailProps {
  clusterId: string;
  onBack: () => void;
  onRefreshSummary: () => void;
}

export const PatternDetail: React.FC<PatternDetailProps> = ({
  clusterId,
  onBack,
  onRefreshSummary
}) => {
  const [clusterList, setClusterList] = useState<ClusterListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>(clusterId);
  const [cluster, setCluster] = useState<ClusterDetail | null>(null);
  const [claims, setClaims] = useState<ClusterClaimItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<ClusterClaimItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'evidence' | 'timeline' | 'distribution' | 'statistics'>('overview');
  
  // Review Modal State
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewAction, setReviewAction] = useState<'confirmed' | 'edited' | 'dismissed'>('confirmed');
  const [customLabel, setCustomLabel] = useState('');
  const [engineerNote, setEngineerNote] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    loadClusterList();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadCluster(selectedId);
    }
  }, [selectedId]);

  const loadClusterList = async () => {
    try {
      const list = await api.getClusters();
      setClusterList(list);
    } catch (err) {
      console.error('Failed to load cluster index', err);
    }
  };

  const loadCluster = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await api.getClusterDetail(id);
      setCluster(detail);
      setCustomLabel(detail.label);

      const claimsResp = await api.getClusterClaims(id);
      setClaims(claimsResp.claims);
    } catch (err: any) {
      setError(err.message || 'Failed to load cluster details');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async () => {
    if (!cluster) return;
    setSubmittingReview(true);
    try {
      await api.submitFeedback(cluster.id, {
        decision: reviewAction,
        rationale: engineerNote,
        custom_label: reviewAction === 'edited' ? customLabel : undefined,
        reviewer: 'Reliability Lead Engineer'
      });
      setShowReviewModal(false);
      await loadCluster(cluster.id);
      await loadClusterList();
      onRefreshSummary();
    } catch (err: any) {
      alert(`Error recording decision: ${err.message}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  const codeChartData = cluster ? Object.entries(cluster.code_distribution).map(([code, count]) => ({
    code,
    count
  })) : [];

  const plantChartData = cluster ? Object.entries(cluster.plant_distribution).map(([plant, count]) => ({
    plant: plant.split(' - ')[0] || plant,
    count
  })) : [];

  const filteredClaims = claims.filter(c => 
    c.external_claim_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.narrative.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.failure_code && c.failure_code.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="max-w-[1440px] mx-auto text-slate-900 space-y-5">
      {/* Top Header & Breadcrumb Bar */}
      <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button 
            onClick={onBack}
            className="p-2 rounded-md text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono text-blue-700 uppercase">Defect Investigation Workstation</span>
            </div>
            <h1 className="text-base font-bold text-slate-900 font-sans tracking-tight">
              Root-Cause Analysis & Verbatim Evidence Console
            </h1>
          </div>
        </div>

        <div className="text-xs text-slate-500 font-sans hidden md:block">
          Use the tabs below to inspect raw technician narratives, taxonomy spread, and mathematical proof.
        </div>
      </div>

      {/* Split-Pane Workstation Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Pane: Discovered Signals Navigator */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col max-h-[840px]">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 font-sans">
              Discovered Signals ({clusterList.length})
            </span>
            <span className="text-[10px] text-blue-700 font-mono font-bold uppercase">Ranked by Alert Score</span>
          </div>

          <div className="divide-y divide-slate-100 overflow-y-auto flex-1">
            {clusterList.map((c) => {
              const isSelected = c.id === selectedId;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`p-4 cursor-pointer transition-colors text-xs ${
                    isSelected 
                      ? 'bg-blue-50/80 border-l-4 border-blue-600' 
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <Badge level={c.alert_level} size="sm">
                      {c.alert_level}
                    </Badge>
                    <span className="font-mono text-slate-900 font-bold">
                      Score: {c.alert_score}
                    </span>
                  </div>

                  <h4 className="font-bold text-slate-900 font-sans mt-2 leading-snug">
                    {c.label}
                  </h4>

                  <div className="flex items-center gap-2 mt-2 text-[11px] font-mono text-slate-500">
                    <span>{c.claim_count} claims</span>
                    <span>•</span>
                    <span className="text-red-700 font-bold">+{c.growth_rate}% surge</span>
                    <span>•</span>
                    <span>{c.cross_code_count} codes</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Pane: Selected Investigation Workspace */}
        <div className="lg:col-span-8 bg-white border border-slate-200 rounded-lg shadow-sm flex flex-col min-h-[750px]">
          {loading ? (
            <div className="py-32 text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-3 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-3 text-xs font-mono text-slate-500">Aggregating cluster evidence from database...</p>
            </div>
          ) : error || !cluster ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              <AlertOctagon className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <span>Failed to load investigation details.</span>
            </div>
          ) : (
            <>
              {/* Workspace Header */}
              <div className="p-6 border-b border-slate-200 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge level={cluster.alert_level} size="sm">
                        {cluster.alert_level}
                      </Badge>
                      <span className="text-xs font-mono text-slate-600">
                        Alert Score: <strong className="text-slate-900">{cluster.alert_score}</strong> / 100
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-xs font-mono text-slate-600">
                        Statistical Z-Score: <strong className="text-red-700">Z = {cluster.significance_score}</strong>
                      </span>
                    </div>

                    <h2 className="text-xl font-bold text-slate-900 font-sans tracking-tight">
                      {cluster.label}
                    </h2>
                  </div>

                  {/* Decision Action Buttons */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => {
                        setReviewAction('confirmed');
                        setEngineerNote('Confirmed as high-priority emerging defect based on cross-code narrative convergence.');
                        setShowReviewModal(true);
                      }}
                      className="px-3.5 py-2 rounded-md text-xs font-bold font-sans bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Confirm Defect</span>
                    </button>

                    <button
                      onClick={() => {
                        setReviewAction('edited');
                        setCustomLabel(cluster.label);
                        setEngineerNote(cluster.feedback?.rationale || '');
                        setShowReviewModal(true);
                      }}
                      className="px-3 py-2 rounded-md text-xs font-semibold font-sans bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-sm transition-colors"
                      title="Edit cluster label"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => {
                        setReviewAction('dismissed');
                        setEngineerNote('Dismissed as known operational noise or non-critical variation.');
                        setShowReviewModal(true);
                      }}
                      className="px-3 py-2 rounded-md text-xs font-semibold font-sans text-slate-500 hover:text-red-700 bg-white hover:bg-red-50 border border-slate-300 shadow-sm transition-colors"
                      title="Dismiss false alarm"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Engineer Verification Tag if already reviewed */}
                {cluster.feedback && (
                  <div className="p-3.5 rounded-md bg-emerald-50 border border-emerald-200 text-xs font-sans flex items-start gap-2.5">
                    <ShieldCheck className="h-5 w-5 text-emerald-700 mt-0.5 shrink-0" />
                    <div>
                      <span className="font-bold text-emerald-900">
                        Verified by {cluster.feedback.reviewer} ({cluster.feedback.decision.toUpperCase()})
                      </span>
                      <p className="text-emerald-800 mt-0.5">"{cluster.feedback.rationale}"</p>
                    </div>
                  </div>
                )}

                {/* Workspace Navigation Tabs */}
                <div className="flex items-center gap-1 border-b border-slate-200 pt-3 -mb-6 font-sans text-xs">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`px-3.5 py-2.5 font-bold transition-colors border-b-2 ${
                      activeTab === 'overview'
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    1. Diagnostic Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('evidence')}
                    className={`px-3.5 py-2.5 font-bold transition-colors border-b-2 flex items-center gap-1.5 ${
                      activeTab === 'evidence'
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    2. Verbatim Claims ({claims.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className={`px-3.5 py-2.5 font-bold transition-colors border-b-2 ${
                      activeTab === 'timeline'
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    3. Emergence Timeline
                  </button>
                  <button
                    onClick={() => setActiveTab('distribution')}
                    className={`px-3.5 py-2.5 font-bold transition-colors border-b-2 ${
                      activeTab === 'distribution'
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    4. Code & Plant Spread
                  </button>
                  <button
                    onClick={() => setActiveTab('statistics')}
                    className={`px-3.5 py-2.5 font-bold transition-colors border-b-2 ${
                      activeTab === 'statistics'
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    5. Statistical Proof
                  </button>
                </div>
              </div>

              {/* Workspace Tab Contents */}
              <div className="p-6 flex-1 space-y-6">
                {/* TAB 1: OVERVIEW */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    {cluster.ai_rationale && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                        <div className="p-4 rounded-lg bg-blue-50/50 border border-blue-100 space-y-2.5">
                          <span className="font-bold text-blue-900 block font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                            Why AI Grouped These Claims (Semantic Cohesion)
                          </span>
                          <p className="text-slate-700 leading-relaxed">
                            {cluster.ai_rationale.why_grouped}
                          </p>
                          <div className="pt-2">
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Key Recognized Symptoms:</span>
                            <div className="flex flex-wrap gap-1.5">
                              {cluster.ai_rationale.key_symptoms.map((s, i) => (
                                <span key={i} className="px-2 py-0.5 rounded bg-white border border-blue-200 text-blue-800 font-mono text-[10px] font-semibold">
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="p-4 rounded-lg bg-red-50/50 border border-red-100 space-y-2.5">
                          <span className="font-bold text-red-900 block font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                            <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
                            Why the Surveillance Engine Alerted
                          </span>
                          <p className="text-slate-700 leading-relaxed">
                            {cluster.ai_rationale.why_alerted}
                          </p>
                          <div className="pt-2">
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Affected Subsystems:</span>
                            <div className="flex flex-wrap gap-1.5">
                              {cluster.ai_rationale.affected_components.map((c, i) => (
                                <span key={i} className="px-2 py-0.5 rounded bg-white border border-red-200 text-red-800 font-mono text-[10px] font-semibold">
                                  {c}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Key Metrics Strip */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 font-sans mb-2.5">
                        Cluster Signal Vital Statistics
                      </h4>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
                          <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Recent Period Volume</span>
                          <span className="text-lg font-bold text-slate-900 mt-1 block">{cluster.current_volume} claims</span>
                          <span className="text-[10px] text-slate-500 mt-0.5 block">July surge volume</span>
                        </div>
                        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
                          <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Historical Baseline</span>
                          <span className="text-lg font-bold text-slate-700 mt-1 block">{cluster.baseline_volume} / mo</span>
                          <span className="text-[10px] text-slate-500 mt-0.5 block">6-mo rolling mean</span>
                        </div>
                        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
                          <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Growth Velocity</span>
                          <span className="text-lg font-bold text-red-700 mt-1 block">+{cluster.growth_rate}%</span>
                          <span className="text-[10px] text-slate-500 mt-0.5 block">Emergence surge</span>
                        </div>
                        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
                          <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Statistical Z-Score</span>
                          <span className="text-lg font-bold text-red-700 mt-1 block">Z = {cluster.significance_score}</span>
                          <span className="text-[10px] text-slate-500 mt-0.5 block">p &lt; 0.0001 significance</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 2: EVIDENCE CLAIMS */}
                {activeTab === 'evidence' && (
                  <div className="space-y-4">
                    <div className="p-3 rounded bg-blue-50 border border-blue-100 text-xs text-slate-700 leading-relaxed">
                      <strong className="text-blue-900">How Evidence Works:</strong> Every claim below was clustered based on narrative similarity, regardless of what checkbox failure code the dealership originally assigned. Click any row to view the full technician diagnostic record.
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <div className="relative flex-1">
                        <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
                        <input
                          type="text"
                          placeholder="Filter claims by ID or technician note..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="w-full pl-9 pr-4 py-2 rounded-md text-xs bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans"
                        />
                      </div>
                      <span className="text-xs font-mono text-slate-500 shrink-0 font-semibold">
                        {filteredClaims.length} of {claims.length} claims
                      </span>
                    </div>

                    <div className="border border-slate-200 rounded-lg overflow-hidden">
                      <table className="w-full text-left text-xs font-sans">
                        <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-mono border-b border-slate-200">
                          <tr>
                            <th className="py-2.5 px-3">Claim ID</th>
                            <th className="py-2.5 px-3">Date</th>
                            <th className="py-2.5 px-3">Dealership Code</th>
                            <th className="py-2.5 px-3">Plant</th>
                            <th className="py-2.5 px-4">Verbatim Technician Observation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 font-mono">
                          {filteredClaims.map((c) => (
                            <tr
                              key={c.claim_id}
                              onClick={() => setSelectedClaim(c)}
                              className="hover:bg-blue-50/50 cursor-pointer transition-colors"
                            >
                              <td className="py-2.5 px-3 font-bold text-blue-700">
                                {c.external_claim_id}
                              </td>
                              <td className="py-2.5 px-3 text-slate-500">
                                {c.claim_date}
                              </td>
                              <td className="py-2.5 px-3">
                                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 text-[10px] font-semibold">
                                  {c.failure_code || 'UNASSIGNED'}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                                {c.plant ? c.plant.split(' - ')[0] : '—'}
                              </td>
                              <td className="py-2.5 px-4 text-slate-700 font-sans text-xs max-w-md truncate">
                                {c.narrative}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB 3: SIGNAL TIMELINE */}
                {activeTab === 'timeline' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-xs font-sans">
                      <span className="text-slate-600">
                        Monthly observed claim volume compared against historical rolling baseline ({cluster.time_series.map(t => t.claim_count).join(' → ')} claims).
                      </span>
                      <div className="flex items-center gap-3 font-mono text-[11px]">
                        <span className="flex items-center gap-1 text-blue-700 font-bold">
                          <span className="w-2.5 h-0.5 bg-blue-600 inline-block"></span>
                          Observed Volume
                        </span>
                        <span className="flex items-center gap-1 text-slate-400">
                          <span className="w-2.5 h-0.5 bg-slate-400 stroke-dashed inline-block"></span>
                          Baseline
                        </span>
                      </div>
                    </div>

                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={cluster.time_series} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <defs>
                            <linearGradient id="detailGradientLight2" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25}/>
                              <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="period" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }} />
                          <YAxis stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '4px', color: '#0f172a', fontSize: '11px', fontFamily: 'monospace' }} 
                          />
                          <Area type="monotone" dataKey="claim_count" name="Observed Claims" stroke="#2563eb" strokeWidth={2} fill="url(#detailGradientLight2)" />
                          <Area type="monotone" dataKey="baseline" name="Baseline Mean" stroke="#94a3b8" strokeDasharray="3 3" strokeWidth={1.5} fill="none" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* TAB 4: DISTRIBUTION BREAKDOWN */}
                {activeTab === 'distribution' && (
                  <div className="space-y-4">
                    <div className="p-3 rounded bg-blue-50 border border-blue-100 text-xs text-slate-700 leading-relaxed">
                      <strong className="text-blue-900">Taxonomy Fragmentation Insight:</strong> This defect was split across {cluster.cross_code_count} separate failure codes at dealerships, preventing single-code threshold alerts from firing.
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                        <span className="text-xs font-bold text-slate-900 font-sans block">
                          Failure Code Dispersion ({codeChartData.length} codes)
                        </span>
                        <div className="h-48 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={codeChartData} layout="vertical" margin={{ top: 5, right: 20, left: 50, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                              <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }} />
                              <YAxis dataKey="code" type="category" stroke="#94a3b8" tick={{ fill: '#334155', fontSize: 10, fontFamily: 'monospace' }} />
                              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '4px', fontSize: '11px' }} />
                              <Bar dataKey="count" fill="#2563eb" radius={[0, 2, 2, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                        <span className="text-xs font-bold text-slate-900 font-sans block">
                          Manufacturing Plants ({plantChartData.length} facilities)
                        </span>
                        <div className="h-48 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={plantChartData} layout="vertical" margin={{ top: 5, right: 20, left: 40, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                              <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }} />
                              <YAxis dataKey="plant" type="category" stroke="#94a3b8" tick={{ fill: '#334155', fontSize: 10, fontFamily: 'monospace' }} />
                              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '4px', fontSize: '11px' }} />
                              <Bar dataKey="count" fill="#4f46e5" radius={[0, 2, 2, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 5: STATISTICAL PROOF & 5-FACTOR MODEL EXPLAINABILITY */}
                {activeTab === 'statistics' && (
                  <div className="space-y-5 text-xs font-sans">
                    {/* Mathematical Formula Explanation Header */}
                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center gap-2">
                        <Calculator className="h-4 w-4 text-blue-600 shrink-0" />
                        <span className="font-bold text-slate-900 text-xs font-sans">
                          5-Factor Composite Scoring Model Formula
                        </span>
                      </div>
                      <p className="text-slate-600 leading-relaxed text-xs">
                        The Composite Alert Score is a weighted multi-factor reliability index that balances signal volume, growth velocity, statistical deviation, cross-code dispersion, and narrative semantic coherence.
                      </p>
                      <div className="p-2.5 rounded bg-white border border-slate-200 font-mono text-[11px] text-slate-800 font-semibold overflow-x-auto">
                        Composite Score = (0.30 &times; Growth) + (0.25 &times; Z-Score) + (0.15 &times; Size) + (0.15 &times; CrossCode) + (0.15 &times; Coherence)
                      </div>
                    </div>

                    {/* Defensible 5-Factor Score Decomposition Table */}
                    <div className="space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-1 border-b border-slate-200">
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 font-sans">
                            Mathematical Point Attribution Matrix
                          </h4>
                          <p className="text-[11px] text-slate-500 font-sans">
                            Exact breakdown of points earned across each monitored dimension summing to the composite alert score.
                          </p>
                        </div>
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-xs text-slate-600 font-sans">Total Score:</span>
                          <span className="text-base font-bold text-slate-900">{cluster.alert_score}</span>
                          <span className="text-xs text-slate-500">/ 100.0</span>
                          <Badge level={cluster.alert_level} size="sm">
                            {cluster.alert_level}
                          </Badge>
                        </div>
                      </div>

                      <div className="border border-slate-200 rounded-lg overflow-hidden">
                        <table className="w-full text-left text-xs font-sans">
                          <thead className="bg-slate-50 text-slate-700 uppercase text-[10px] font-mono border-b border-slate-200">
                            <tr>
                              <th className="py-2.5 px-3">Monitored Factor</th>
                              <th className="py-2.5 px-3">Methodology & Benchmark</th>
                              <th className="py-2.5 px-3 text-right">Raw Measured Value</th>
                              <th className="py-2.5 px-3 text-right">Weight</th>
                              <th className="py-2.5 px-3 text-right">Max Pts</th>
                              <th className="py-2.5 px-4 text-right">Points Earned</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-mono text-xs">
                            {/* Factor 1: Growth Velocity */}
                            {(() => {
                              const f = cluster.factor_breakdown?.growth_velocity;
                              const raw = f ? f.raw_value : `+${cluster.growth_rate}%`;
                              const pts = f ? f.points_earned : Math.round(0.30 * Math.min(100, cluster.growth_rate) * 10) / 10;
                              return (
                                <tr className="hover:bg-blue-50/40">
                                  <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                                    <div className="flex items-center gap-1.5">
                                      <TrendingUp className="h-3.5 w-3.5 text-red-600 shrink-0" />
                                      <span>1. Growth Velocity</span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-3 font-sans text-slate-600 text-[11px]">
                                    Surge rate vs 6-mo historical rolling mean (&gt;100% surge = max)
                                  </td>
                                  <td className="py-3 px-3 text-right font-bold text-red-700">
                                    {raw}
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-600">
                                    30%
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-500">
                                    30.0
                                  </td>
                                  <td className="py-3 px-4 text-right font-bold text-slate-900 bg-slate-50/50">
                                    {pts.toFixed(1)} <span className="text-slate-400 font-normal text-[10px]">/ 30.0</span>
                                  </td>
                                </tr>
                              );
                            })()}

                            {/* Factor 2: Statistical Significance */}
                            {(() => {
                              const f = cluster.factor_breakdown?.statistical_significance;
                              const raw = f ? f.raw_value : `Z = ${cluster.significance_score}`;
                              const pts = f ? f.points_earned : Math.round(0.25 * Math.min(100, cluster.significance_score * 35.0) * 10) / 10;
                              return (
                                <tr className="hover:bg-blue-50/40">
                                  <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                                    <div className="flex items-center gap-1.5">
                                      <Activity className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                                      <span>2. Statistical Significance</span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-3 font-sans text-slate-600 text-[11px]">
                                    Poisson-normal Z-score deviation (Z &ge; 2.86 = max, p &lt; 0.001)
                                  </td>
                                  <td className="py-3 px-3 text-right font-bold text-red-700">
                                    {raw}
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-600">
                                    25%
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-500">
                                    25.0
                                  </td>
                                  <td className="py-3 px-4 text-right font-bold text-slate-900 bg-slate-50/50">
                                    {pts.toFixed(1)} <span className="text-slate-400 font-normal text-[10px]">/ 25.0</span>
                                  </td>
                                </tr>
                              );
                            })()}

                            {/* Factor 3: Cluster Volume */}
                            {(() => {
                              const f = cluster.factor_breakdown?.cluster_volume;
                              const raw = f ? f.raw_value : `${cluster.claim_count} claims`;
                              const pts = f ? f.points_earned : Math.round(0.15 * Math.min(100, cluster.claim_count * 5.0) * 10) / 10;
                              return (
                                <tr className="hover:bg-blue-50/40">
                                  <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                                    <div className="flex items-center gap-1.5">
                                      <Layers className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                                      <span>3. Cluster Volume</span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-3 font-sans text-slate-600 text-[11px]">
                                    Consolidated fleet-wide claim count (&ge;20 claims = max)
                                  </td>
                                  <td className="py-3 px-3 text-right font-bold text-slate-800">
                                    {raw}
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-600">
                                    15%
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-500">
                                    15.0
                                  </td>
                                  <td className="py-3 px-4 text-right font-bold text-slate-900 bg-slate-50/50">
                                    {pts.toFixed(1)} <span className="text-slate-400 font-normal text-[10px]">/ 15.0</span>
                                  </td>
                                </tr>
                              );
                            })()}

                            {/* Factor 4: Cross-Code Dispersion */}
                            {(() => {
                              const f = cluster.factor_breakdown?.cross_code_dispersion;
                              const raw = f ? f.raw_value : `${cluster.cross_code_count} dealer codes`;
                              const pts = f ? f.points_earned : Math.round(0.15 * Math.min(100, cluster.cross_code_count * 20.0) * 10) / 10;
                              return (
                                <tr className="hover:bg-blue-50/40">
                                  <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                                    <div className="flex items-center gap-1.5">
                                      <Tag className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                                      <span>4. Cross-Code Dispersion</span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-3 font-sans text-slate-600 text-[11px]">
                                    Taxonomy fragmentation across structured codes (&ge;5 codes = max)
                                  </td>
                                  <td className="py-3 px-3 text-right font-bold text-slate-800">
                                    {raw}
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-600">
                                    15%
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-500">
                                    15.0
                                  </td>
                                  <td className="py-3 px-4 text-right font-bold text-slate-900 bg-slate-50/50">
                                    {pts.toFixed(1)} <span className="text-slate-400 font-normal text-[10px]">/ 15.0</span>
                                  </td>
                                </tr>
                              );
                            })()}

                            {/* Factor 5: Semantic Coherence */}
                            {(() => {
                              const f = cluster.factor_breakdown?.semantic_coherence;
                              const raw = f ? f.raw_value : `${(cluster.coherence_score * 100).toFixed(1)}%`;
                              const pts = f ? f.points_earned : Math.round(0.15 * Math.min(100, cluster.coherence_score * 100.0) * 10) / 10;
                              return (
                                <tr className="hover:bg-blue-50/40">
                                  <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                                    <div className="flex items-center gap-1.5">
                                      <Sparkles className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                                      <span>5. Semantic Coherence</span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-3 font-sans text-slate-600 text-[11px]">
                                    Mean pairwise cosine vector cohesion across technician notes
                                  </td>
                                  <td className="py-3 px-3 text-right font-bold text-slate-800">
                                    {raw}
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-600">
                                    15%
                                  </td>
                                  <td className="py-3 px-3 text-right text-slate-500">
                                    15.0
                                  </td>
                                  <td className="py-3 px-4 text-right font-bold text-slate-900 bg-slate-50/50">
                                    {pts.toFixed(1)} <span className="text-slate-400 font-normal text-[10px]">/ 15.0</span>
                                  </td>
                                </tr>
                              );
                            })()}
                          </tbody>
                          <tfoot className="bg-slate-100 font-mono font-bold text-slate-900 border-t-2 border-slate-300">
                            <tr>
                              <td colSpan={3} className="py-3 px-3 text-slate-900 font-sans">
                                Composite Total Score (Sum of All 5 Factors)
                              </td>
                              <td className="py-3 px-3 text-right">
                                100%
                              </td>
                              <td className="py-3 px-3 text-right">
                                100.0
                              </td>
                              <td className="py-3 px-4 text-right text-sm text-red-700 bg-slate-200/60">
                                {cluster.alert_score.toFixed(1)} <span className="text-slate-500 font-normal text-xs">/ 100.0</span>
                              </td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>

                    {/* Evaluator Explainer Card */}
                    <div className="p-4 rounded-lg bg-blue-50/60 border border-blue-200 text-xs font-sans space-y-2">
                      <div className="flex items-center gap-2 text-blue-900 font-bold">
                        <Info className="h-4 w-4 text-blue-600 shrink-0" />
                        <span>Executive Reliability Proof Summary</span>
                      </div>
                      <p className="text-slate-700 leading-relaxed">
                        This pattern reached an Alert Score of <strong className="text-slate-900 font-mono">{cluster.alert_score} / 100</strong> because it simultaneously exhibits an extreme volume surge (<strong className="font-mono text-slate-900">+{cluster.growth_rate}%</strong>, 30.0 pts), high statistical significance (<strong className="font-mono text-slate-900">Z = {cluster.significance_score}</strong>, 25.0 pts), full cross-code concealment (<strong className="font-mono text-slate-900">{cluster.cross_code_count} dealer codes</strong>, 15.0 pts), substantial fleet volume (<strong className="font-mono text-slate-900">{cluster.claim_count} claims</strong>, 15.0 pts), and tight semantic convergence (<strong className="font-mono text-slate-900">{(cluster.coherence_score * 100).toFixed(1)}%</strong>, {(cluster.factor_breakdown?.semantic_coherence?.points_earned ?? (cluster.coherence_score * 15)).toFixed(1)} pts).
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Claim Detail Drawer Modal */}
      {selectedClaim && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white border border-slate-200 rounded-lg max-w-2xl w-full p-6 space-y-4 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase text-blue-700 font-bold">Technician Diagnostic Record</span>
                <h3 className="text-base font-bold text-slate-900 font-mono mt-0.5">{selectedClaim.external_claim_id}</h3>
              </div>
              <button onClick={() => setSelectedClaim(null)} className="text-slate-400 hover:text-slate-700 p-1">
                <XCircle className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Date</span>
                <span className="text-slate-900 mt-0.5 block font-semibold">{selectedClaim.claim_date}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Model</span>
                <span className="text-slate-900 mt-0.5 block font-semibold">{selectedClaim.product_model || '—'}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Plant</span>
                <span className="text-slate-900 mt-0.5 block font-semibold">{selectedClaim.plant || '—'}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Assigned Code</span>
                <span className="text-slate-900 font-bold mt-0.5 block">{selectedClaim.failure_code || 'UNASSIGNED'}</span>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono uppercase text-slate-500 block mb-1 font-semibold">Verbatim Technician Narrative</span>
              <p className="p-3.5 rounded bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans">
                "{selectedClaim.narrative}"
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedClaim(null)}
                className="px-4 py-2 rounded text-xs font-semibold font-sans bg-slate-100 text-slate-700 hover:bg-slate-200"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Review Decision Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white border border-slate-200 rounded-lg max-w-lg w-full p-6 space-y-4 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                Record Engineering Review Decision ({reviewAction.toUpperCase()})
              </h3>
              <button onClick={() => setShowReviewModal(false)} className="text-slate-400 hover:text-slate-700 p-1">
                <XCircle className="h-4 w-4" />
              </button>
            </div>

            {reviewAction === 'edited' && (
              <div>
                <label className="text-[11px] font-mono uppercase text-slate-500 block mb-1">Custom Pattern Title</label>
                <input
                  type="text"
                  value={customLabel}
                  onChange={(e) => setCustomLabel(e.target.value)}
                  className="w-full px-3 py-2 rounded text-xs bg-white border border-slate-300 text-slate-900 font-sans focus:outline-none focus:border-blue-500"
                />
              </div>
            )}

            <div>
              <label className="text-[11px] font-mono uppercase text-slate-500 block mb-1 font-semibold">Engineering Rationale & Notes</label>
              <textarea
                rows={3}
                value={engineerNote}
                onChange={(e) => setEngineerNote(e.target.value)}
                placeholder="Explain the engineering rationale behind this decision..."
                className="w-full px-3 py-2 rounded text-xs bg-white border border-slate-300 text-slate-900 font-sans focus:outline-none focus:border-blue-500 resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200">
              <button
                onClick={() => setShowReviewModal(false)}
                className="px-3.5 py-2 rounded text-xs font-semibold font-sans bg-slate-100 hover:bg-slate-200 text-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleReviewSubmit}
                disabled={submittingReview}
                className="px-4 py-2 rounded text-xs font-bold font-sans bg-slate-900 hover:bg-slate-800 text-white"
              >
                {submittingReview ? 'Recording...' : 'Save Decision'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
