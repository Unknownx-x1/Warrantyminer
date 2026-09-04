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
                        Monthly observed claim volume compared against historical rolling baseline (1 &rarr; 1 &rarr; 2 &rarr; 2 &rarr; 4 &rarr; 8 &rarr; 17 claims).
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
                      <strong className="text-blue-900">Taxonomy Fragmentation Insight:</strong> This defect was split across 5 separate failure codes at dealerships, preventing single-code threshold alerts from firing.
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

                {/* TAB 5: STATISTICAL PROOF */}
                {activeTab === 'statistics' && (
                  <div className="space-y-4 font-mono text-xs">
                    <div className="p-3 rounded bg-slate-50 border border-slate-200 text-xs font-sans text-slate-700 leading-relaxed">
                      <strong className="text-slate-900">5-Factor Formula:</strong> Score = <span className="font-mono font-semibold">(0.30 &times; Growth) + (0.25 &times; Z-Score) + (0.15 &times; Size) + (0.15 &times; CrossCode) + (0.15 &times; Coherence)</span>
                    </div>

                    <div className="flex items-center justify-between pb-2 border-b border-slate-200 font-sans">
                      <span className="text-xs font-bold text-slate-900">
                        Decomposition Matrix (Final Score: {cluster.alert_score} / 100)
                      </span>
                      <span className="font-mono text-red-700 font-bold">
                        {cluster.alert_level}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">1. Growth (30%)</span>
                        <span className="text-sm font-bold text-red-700 mt-1 block">+{cluster.growth_rate}%</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Norm: {Math.min(100, Math.round(cluster.growth_rate))} / 100</span>
                      </div>

                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">2. Z-Score (25%)</span>
                        <span className="text-sm font-bold text-red-700 mt-1 block">Z = {cluster.significance_score}</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Norm: {Math.min(100, Math.round(cluster.significance_score * 30))} / 100</span>
                      </div>

                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">3. Size (15%)</span>
                        <span className="text-sm font-bold text-slate-900 mt-1 block">{cluster.claim_count} claims</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Norm: {Math.min(100, cluster.claim_count * 4)} / 100</span>
                      </div>

                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">4. Cross-Code (15%)</span>
                        <span className="text-sm font-bold text-slate-900 mt-1 block">{cluster.cross_code_count} codes</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Norm: {Math.min(100, cluster.cross_code_count * 20)} / 100</span>
                      </div>

                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">5. Coherence (15%)</span>
                        <span className="text-sm font-bold text-slate-900 mt-1 block">{(cluster.coherence_score * 100).toFixed(1)}%</span>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Cosine Cohesion</span>
                      </div>
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
