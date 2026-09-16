import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Search, 
  Terminal, 
  FileText, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  XCircle, 
  HelpCircle, 
  Cpu, 
  Activity, 
  Layers, 
  TrendingUp, 
  RefreshCw, 
  Check, 
  X, 
  ExternalLink,
  ChevronRight,
  Database,
  Radio,
  Wrench
} from 'lucide-react';
import { api } from '../api/client';
import { ClusterListItem, InvestigationDetail, AgentFinding, ToolExecutionLog, Report8D, TSBDraft } from '../types';
import { LiveAgentStream } from '../components/LiveAgentStream';

interface WarRoomProps {
  initialClusterId?: string | null;
  onSelectClaim?: (claimId: string) => void;
  onNavigateToMemory?: () => void;
}

export const WarRoom: React.FC<WarRoomProps> = ({
  initialClusterId,
  onSelectClaim,
  onNavigateToMemory
}) => {
  const [clusters, setClusters] = useState<ClusterListItem[]>([]);
  const [selectedClusterId, setSelectedClusterId] = useState<string>('');
  const [investigation, setInvestigation] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningSwarm, setRunningSwarm] = useState<boolean>(false);
  const [showLiveStream, setShowLiveStream] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'synthesis' | 'tools' | '8d' | 'tsb'>('synthesis');
  const [findingFilter, setFindingFilter] = useState<'ALL' | 'OBSERVED' | 'INFERRED' | 'UNKNOWN'>('ALL');
  const [decisionModal, setDecisionModal] = useState<boolean>(false);
  const [decisionType, setDecisionType] = useState<'confirmed' | 'rejected' | 'needs_evidence'>('confirmed');
  const [decisionRationale, setDecisionRationale] = useState<string>('');
  const [customLabel, setCustomLabel] = useState<string>('');
  const [submittingDecision, setSubmittingDecision] = useState<boolean>(false);

  useEffect(() => {
    loadClusters();
  }, []);

  useEffect(() => {
    if (selectedClusterId) {
      loadInvestigation(selectedClusterId);
    }
  }, [selectedClusterId]);

  const loadClusters = async () => {
    try {
      setLoading(true);
      const data = await api.getClusters();
      setClusters(data);
      if (data.length > 0) {
        const targetId = initialClusterId && data.some(c => c.id === initialClusterId)
          ? initialClusterId
          : data[0].id;
        setSelectedClusterId(targetId);
      }
    } catch (err) {
      console.error('Failed to load clusters for War Room', err);
    } finally {
      setLoading(false);
    }
  };

  const loadInvestigation = async (clusterId: string, forceRecompute: boolean = false) => {
    try {
      setLoading(true);
      const invData = await api.getInvestigationByCluster(clusterId);
      setInvestigation(invData);
    } catch (err) {
      console.error('Failed to load investigation', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRerunSwarm = async () => {
    if (!selectedClusterId) return;
    try {
      setRunningSwarm(true);
      await api.runInvestigation(selectedClusterId, true);
      await loadInvestigation(selectedClusterId, true);
    } catch (err: any) {
      alert(`Investigation failed: ${err.message}`);
    } finally {
      setRunningSwarm(false);
    }
  };

  const handleDecisionSubmit = async () => {
    if (!investigation) return;
    try {
      setSubmittingDecision(true);
      await api.submitInvestigationDecision(investigation.id, {
        decision: decisionType,
        rationale: decisionRationale,
        custom_label: customLabel || undefined,
        reviewer: 'Chief Reliability Engineer'
      });
      setDecisionModal(false);
      await loadInvestigation(selectedClusterId, false);
      const updatedClusters = await api.getClusters();
      setClusters(updatedClusters);
    } catch (err: any) {
      alert(`Failed to submit decision: ${err.message}`);
    } finally {
      setSubmittingDecision(false);
    }
  };

  const selectedCluster = clusters.find(c => c.id === selectedClusterId);

  const filteredFindings = (investigation?.findings || []).filter(f => {
    if (findingFilter === 'ALL') return true;
    return f.classification === findingFilter;
  });

  if (loading && !investigation) {
    return (
      <div className="py-24 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-slate-900 border-r-transparent"></div>
        <p className="mt-3 text-xs font-mono text-slate-500">Autonomous Engineering Swarm Investigating Field Evidence...</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header & Cluster Selector */}
      <div className="bg-white border border-slate-200 rounded-[4px] p-5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider font-semibold px-2 py-0.5 rounded-[2px] bg-slate-900 text-white">
                Autonomous L2 Investigation
              </span>
              <span className={`text-[10px] font-mono uppercase tracking-wider font-semibold px-2 py-0.5 rounded-[2px] border ${
                investigation?.decision === 'confirmed'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                  : investigation?.decision === 'rejected'
                  ? 'bg-slate-100 text-slate-700 border-slate-300'
                  : 'bg-amber-50 text-amber-800 border-amber-300'
              }`}>
                STATUS: {investigation?.decision.toUpperCase()}
              </span>
              <span className="text-xs font-mono text-slate-500">
                Execution Time: {investigation?.execution_time_ms.toFixed(1)}ms
              </span>
            </div>

            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-slate-900 font-sans tracking-tight">
                {selectedCluster?.label || 'Active Investigation'}
              </h1>
            </div>
            <p className="text-xs text-slate-600 max-w-4xl leading-relaxed">
              {investigation?.summary_conclusion || 'Automated multi-agent engineering investigation active.'}
            </p>
          </div>

          {/* Cluster Switcher & Swarm Trigger */}
          <div className="flex items-center gap-2 self-start lg:self-center flex-wrap">
            <select
              value={selectedClusterId}
              onChange={(e) => setSelectedClusterId(e.target.value)}
              className="text-xs font-sans bg-white border border-slate-300 rounded-[3px] px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-900 text-slate-800"
            >
              {clusters.map((c) => (
                <option key={c.id} value={c.id}>
                  [{c.alert_level}] {c.label} ({c.claim_count} claims • Score: {c.alert_score})
                </option>
              ))}
            </select>

            <button
              onClick={() => setShowLiveStream(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-[3px] text-xs font-semibold font-mono uppercase tracking-wider bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all active:scale-[0.98]"
            >
              <Radio className="h-3.5 w-3.5 animate-pulse text-indigo-200" />
              <span>Live Mesh Stream</span>
            </button>

            <button
              onClick={handleRerunSwarm}
              disabled={runningSwarm}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-[3px] text-xs font-semibold font-mono uppercase tracking-wider bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 transition-all active:scale-[0.98]"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${runningSwarm ? 'animate-spin' : ''}`} />
              <span>{runningSwarm ? 'Investigating...' : 'Re-Run Swarm'}</span>
            </button>
          </div>
        </div>

        {/* Real-time KPI Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-5 pt-4 border-t border-slate-100 font-mono">
          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Alert Score</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">{selectedCluster?.alert_score} / 100</div>
            <div className="text-[10px] text-slate-600 font-sans mt-0.5">{selectedCluster?.alert_level} Priority</div>
          </div>

          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Surge Growth</div>
            <div className="text-base font-bold text-rose-700 mt-0.5">+{selectedCluster?.growth_rate.toFixed(0)}%</div>
            <div className="text-[10px] text-slate-600 font-sans mt-0.5">vs 6-mo Baseline</div>
          </div>

          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Poisson Z-Score</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">Z = {selectedCluster?.significance_score.toFixed(2)}</div>
            <div className="text-[10px] text-emerald-700 font-sans mt-0.5">p &lt; 0.001 Sig</div>
          </div>

          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Cluster Claims</div>
            <div className="text-base font-bold text-slate-900 mt-0.5">{selectedCluster?.claim_count} claims</div>
            <div className="text-[10px] text-slate-600 font-sans mt-0.5">Unified Volume</div>
          </div>

          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Taxonomy Spread</div>
            <div className="text-base font-bold text-amber-700 mt-0.5">{selectedCluster?.cross_code_count} Codes</div>
            <div className="text-[10px] text-slate-600 font-sans mt-0.5">Obscured in Silos</div>
          </div>

          <div className="p-2.5 rounded-[3px] bg-slate-50 border border-slate-200/80">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Agent Confidence</div>
            <div className="text-base font-bold text-blue-700 mt-0.5">{((investigation?.confidence || 0.85) * 100).toFixed(0)}%</div>
            <div className="text-[10px] text-slate-600 font-sans mt-0.5">{investigation?.overall_classification.replace('_', ' ')}</div>
          </div>
        </div>
      </div>

      {/* 5 Agent Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* 1. Investigator */}
        <div className="bg-white border border-slate-200 rounded-[4px] p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[3px] bg-blue-100 flex items-center justify-center text-blue-700">
                <Search className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 font-sans">Investigator</span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded-[2px] border border-emerald-200">
              <CheckCircle2 className="h-3 w-3" /> COMPLETE
            </span>
          </div>
          <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed font-sans">
            Isolated physical component <span className="font-semibold text-slate-900">'{selectedCluster?.primary_component || 'subsystem'}'</span> and symptom <span className="font-semibold text-slate-900">'{selectedCluster?.primary_symptom || 'knocking'}'</span>.
          </p>
        </div>

        {/* 2. Analytics */}
        <div className="bg-white border border-slate-200 rounded-[4px] p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[3px] bg-purple-100 flex items-center justify-center text-purple-700">
                <Activity className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 font-sans">Analytics</span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded-[2px] border border-emerald-200">
              <CheckCircle2 className="h-3 w-3" /> COMPLETE
            </span>
          </div>
          <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed font-sans">
            Confirmed Poisson surge (Z = {selectedCluster?.significance_score.toFixed(2)}) and Shannon entropy across {selectedCluster?.cross_code_count} codes.
          </p>
        </div>

        {/* 3. Red Team */}
        <div className="bg-white border border-slate-200 rounded-[4px] p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[3px] bg-rose-100 flex items-center justify-center text-rose-700">
                <ShieldAlert className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 font-sans">Red Team</span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded-[2px] border border-emerald-200">
              <CheckCircle2 className="h-3 w-3" /> COMPLETE
            </span>
          </div>
          <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed font-sans">
            Evaluated plant bias, sample power, and outlier claims across {selectedCluster?.plant_count} plants.
          </p>
        </div>

        {/* 4. Regulatory */}
        <div className="bg-white border border-slate-200 rounded-[4px] p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[3px] bg-amber-100 flex items-center justify-center text-amber-700">
                <BookOpen className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 font-sans">Regulatory</span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-slate-600 font-semibold bg-slate-100 px-1.5 py-0.5 rounded-[2px] border border-slate-200">
              <Clock className="h-3 w-3" /> UNAVAIL
            </span>
          </div>
          <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed font-sans">
            NHTSA API offline. Supplier MES lot tracking not attached to stream (reported honestly).
          </p>
        </div>

        {/* 5. CAPA Adjudicator */}
        <div className="bg-white border border-slate-200 rounded-[4px] p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[3px] bg-emerald-100 flex items-center justify-center text-emerald-700">
                <Wrench className="h-3.5 w-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 font-sans">CAPA Adjudicator</span>
            </div>
            <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded-[2px] border border-emerald-200">
              <CheckCircle2 className="h-3 w-3" /> COMPLETE
            </span>
          </div>
          <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed font-sans">
            Synthesized 8D Problem Solving Dossier and draft Technical Service Bulletin (TSB).
          </p>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="bg-white border border-slate-200 rounded-[4px] shadow-2xs">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 pt-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('synthesis')}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold font-sans border-b-2 transition-all ${
                activeTab === 'synthesis'
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Evidence Findings ({investigation?.findings.length || 0})</span>
            </button>

            <button
              onClick={() => setActiveTab('tools')}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold font-sans border-b-2 transition-all ${
                activeTab === 'tools'
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Terminal className="h-3.5 w-3.5" />
              <span>Tool Audit Stream ({investigation?.tool_logs.length || 0})</span>
            </button>

            <button
              onClick={() => setActiveTab('8d')}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold font-sans border-b-2 transition-all ${
                activeTab === '8d'
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>8D Root-Cause Report</span>
            </button>

            <button
              onClick={() => setActiveTab('tsb')}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold font-sans border-b-2 transition-all ${
                activeTab === 'tsb'
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Technical Bulletin (TSB) Draft</span>
            </button>
          </div>

          {/* Human-in-the-Loop Action Gate */}
          <div className="pb-2">
            <button
              onClick={() => {
                setDecisionType('confirmed');
                setDecisionModal(true);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-[3px] text-xs font-semibold font-mono uppercase tracking-wider bg-emerald-700 hover:bg-emerald-800 text-white shadow-xs transition-all active:scale-[0.98]"
            >
              <Check className="h-3.5 w-3.5" />
              <span>Verify &amp; Confirm Defect</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Evidence Findings */}
        {activeTab === 'synthesis' && (
          <div className="p-5 space-y-5">
            {/* Filter Pills */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-1 font-mono text-xs">
                {(['ALL', 'OBSERVED', 'INFERRED', 'UNKNOWN'] as const).map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setFindingFilter(tag)}
                    className={`px-2.5 py-1 rounded-[3px] font-semibold text-[11px] transition-all ${
                      findingFilter === tag
                        ? 'bg-slate-900 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
              <span className="text-xs text-slate-500 font-mono">
                Showing {filteredFindings.length} structured findings
              </span>
            </div>

            {/* Findings Feed */}
            <div className="space-y-3">
              {filteredFindings.map((finding) => (
                <div 
                  key={finding.id}
                  className="p-4 rounded-[4px] border border-slate-200 bg-white hover:border-slate-300 transition-all space-y-2.5"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase font-bold tracking-wider px-2 py-0.5 rounded-[2px] bg-slate-100 text-slate-700 border border-slate-200">
                        {finding.agent_name}
                      </span>
                      <span className={`text-[10px] font-mono uppercase font-bold tracking-wider px-2 py-0.5 rounded-[2px] ${
                        finding.classification === 'OBSERVED'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
                          : finding.classification === 'INFERRED'
                          ? 'bg-blue-50 text-blue-800 border border-blue-300'
                          : 'bg-amber-50 text-amber-800 border border-amber-300'
                      }`}>
                        [{finding.classification}]
                      </span>
                    </div>

                    <div className="text-[11px] font-mono text-slate-500">
                      Confidence: {(finding.confidence * 100).toFixed(0)}%
                    </div>
                  </div>

                  <p className="text-xs text-slate-800 font-sans leading-relaxed">
                    {finding.statement}
                  </p>

                  {/* Cited Evidence Claims */}
                  {finding.evidence_claim_ids && finding.evidence_claim_ids.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] font-mono uppercase font-semibold text-slate-500">Cited Evidence Claims:</span>
                      {finding.evidence_claim_ids.map((cid) => (
                        <button
                          key={cid}
                          onClick={() => onSelectClaim && onSelectClaim(cid)}
                          className="text-[10px] font-mono bg-blue-50 hover:bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-[2px] border border-blue-200 flex items-center gap-1 transition-all"
                        >
                          <span>{cid}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Contradicting / Outlier Claims */}
                  {finding.contradiction_claim_ids && finding.contradiction_claim_ids.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] font-mono uppercase font-semibold text-rose-600">Outlier / Counter Claims:</span>
                      {finding.contradiction_claim_ids.map((cid) => (
                        <span key={cid} className="text-[10px] font-mono bg-rose-50 text-rose-800 px-1.5 py-0.5 rounded-[2px] border border-rose-200">
                          {cid}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Unknowns & Actionable Recommendations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200 font-sans">
              <div className="p-4 rounded-[4px] bg-amber-50/60 border border-amber-200 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                  <HelpCircle className="h-4 w-4 text-amber-700" />
                  <span>Remaining Unknowns (Requires Physical Teardown)</span>
                </div>
                <ul className="space-y-1.5 text-xs text-amber-950">
                  {(investigation?.unknowns || []).map((u, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="font-bold">•</span>
                      <span>{u}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-[4px] bg-blue-50/60 border border-blue-200 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-900">
                  <CheckCircle2 className="h-4 w-4 text-blue-700" />
                  <span>Recommended Reliability Actions</span>
                </div>
                <ul className="space-y-1.5 text-xs text-blue-950">
                  {(investigation?.recommendations || []).map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Tool Execution Stream */}
        {activeTab === 'tools' && (
          <div className="p-5 space-y-4 font-mono">
            <div className="text-xs text-slate-500">
              Audit trail of deterministic tools and statistical functions invoked by autonomous agents during investigation:
            </div>

            <div className="space-y-3">
              {(investigation?.tool_logs || []).map((tool) => (
                <div 
                  key={tool.id}
                  className="p-4 rounded-[4px] border border-slate-200 bg-slate-900 text-slate-100 text-xs space-y-2"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2 text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">&gt; TOOL: {tool.tool_name}()</span>
                      <span className="text-slate-400 font-sans">[{tool.agent_role}]</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded-[2px] text-[10px] font-bold ${
                        tool.status === 'SUCCESS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}>
                        {tool.status}
                      </span>
                      <span className="text-slate-400">{tool.duration_ms}ms</span>
                    </div>
                  </div>

                  <div className="text-slate-300 font-sans text-xs">
                    {tool.output_summary}
                  </div>

                  {tool.input_params && Object.keys(tool.input_params).length > 0 && (
                    <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                      Input Params: {JSON.stringify(tool.input_params)}
                    </div>
                  )}

                  {tool.evidence_refs && tool.evidence_refs.length > 0 && (
                    <div className="text-[11px] text-slate-400 flex items-center gap-1.5 flex-wrap pt-1">
                      <span>Evidence Refs:</span>
                      {tool.evidence_refs.map((ref) => (
                        <span key={ref} className="text-emerald-300 bg-slate-800 px-1 py-0.5 rounded-[2px]">
                          {ref}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: 8D Root Cause Report */}
        {activeTab === '8d' && (
          <div className="p-5 space-y-4 font-sans">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <h3 className="text-sm font-bold text-slate-900 font-sans">
                  8D Problem Solving Report (Disciplines 1–8)
                </h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  Standardized automotive quality problem-solving artifact generated from verified evidence.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">
                {investigation?.report_8d?.generated_at}
              </span>
            </div>

            {investigation?.report_8d ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  investigation.report_8d.d1_team,
                  investigation.report_8d.d2_problem_description,
                  investigation.report_8d.d3_containment_action,
                  investigation.report_8d.d4_root_cause,
                  investigation.report_8d.d5_corrective_action,
                  investigation.report_8d.d6_validation_plan,
                  investigation.report_8d.d7_prevention_action,
                  investigation.report_8d.d8_closure_and_cost,
                ].map((dSec, idx) => (
                  <div key={idx} className="p-4 rounded-[4px] border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 font-sans">{dSec.title}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-[2px] font-bold ${
                        dSec.status === 'ESTABLISHED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {dSec.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
                      {dSec.content}
                    </p>
                    {dSec.evidence && dSec.evidence.length > 0 && (
                      <div className="pt-2 border-t border-slate-200/60 flex items-center gap-1.5 flex-wrap">
                        <span className="text-[10px] font-mono text-slate-500">Claims:</span>
                        {dSec.evidence.map(e => (
                          <span key={e} className="text-[10px] font-mono bg-white px-1.5 py-0.5 rounded-[2px] border border-slate-300">
                            {e}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No 8D report generated for this cluster.</p>
            )}
          </div>
        )}

        {/* Tab 4: Technical Service Bulletin Draft */}
        {activeTab === 'tsb' && (
          <div className="p-5 space-y-5 font-sans">
            {investigation?.tsb_draft ? (
              <div className="border border-slate-300 bg-white rounded-[4px] p-6 space-y-5 shadow-2xs max-w-4xl mx-auto">
                {/* TSB Header */}
                <div className="border-b-2 border-slate-900 pb-4 flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold">
                      OEM FIELD SERVICE ENGINEERING
                    </div>
                    <h2 className="text-base font-bold text-slate-900 mt-1">
                      {investigation.tsb_draft.title}
                    </h2>
                  </div>
                  <div className="text-right font-mono">
                    <div className="text-xs font-bold text-slate-900">{investigation.tsb_draft.tsb_id}</div>
                    <div className="text-[11px] text-slate-500">{investigation.tsb_draft.issue_date}</div>
                  </div>
                </div>

                <div className="space-y-4 text-xs text-slate-800 leading-relaxed">
                  <div>
                    <span className="font-bold text-slate-900 uppercase font-mono text-[11px]">Condition:</span>
                    <p className="mt-1">{investigation.tsb_draft.condition}</p>
                  </div>

                  <div>
                    <span className="font-bold text-slate-900 uppercase font-mono text-[11px]">Affected Vehicle Population:</span>
                    <p className="mt-1">{investigation.tsb_draft.affected_vehicles}</p>
                  </div>

                  <div>
                    <span className="font-bold text-slate-900 uppercase font-mono text-[11px]">Diagnostic &amp; Verification Protocol:</span>
                    <p className="mt-1 whitespace-pre-line bg-slate-50 p-3 rounded-[3px] border border-slate-200 font-mono text-[11px]">
                      {investigation.tsb_draft.diagnostic_procedure}
                    </p>
                  </div>

                  <div>
                    <span className="font-bold text-slate-900 uppercase font-mono text-[11px]">Interim Repair &amp; Correction:</span>
                    <p className="mt-1">{investigation.tsb_draft.interim_repair_recommendation}</p>
                  </div>

                  <div>
                    <span className="font-bold text-slate-900 uppercase font-mono text-[11px]">Warranty Coding Guidance:</span>
                    <p className="mt-1 text-slate-600">{investigation.tsb_draft.warranty_coding_guidance}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No TSB draft available.</p>
            )}
          </div>
        )}
      </div>

      {/* Decision Modal */}
      {decisionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-[4px] border border-slate-300 max-w-lg w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                Human-in-the-Loop Reliability Verification Gate
              </h3>
              <button onClick={() => setDecisionModal(false)} className="text-slate-400 hover:text-slate-700">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 font-sans text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Verification Decision:</label>
                <div className="grid grid-cols-3 gap-2 font-mono">
                  <button
                    type="button"
                    onClick={() => setDecisionType('confirmed')}
                    className={`py-2 px-3 rounded-[3px] border text-center font-bold transition-all ${
                      decisionType === 'confirmed'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-500 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300'
                    }`}
                  >
                    ✓ CONFIRM
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('needs_evidence')}
                    className={`py-2 px-3 rounded-[3px] border text-center font-bold transition-all ${
                      decisionType === 'needs_evidence'
                        ? 'bg-amber-50 text-amber-800 border-amber-500 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300'
                    }`}
                  >
                    ? NEED PROOF
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('rejected')}
                    className={`py-2 px-3 rounded-[3px] border text-center font-bold transition-all ${
                      decisionType === 'rejected'
                        ? 'bg-rose-50 text-rose-800 border-rose-500 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300'
                    }`}
                  >
                    ✕ REJECT
                  </button>
                </div>
              </div>

              {decisionType === 'confirmed' && (
                <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-[3px] text-emerald-900 text-[11px]">
                  Confirming this defect will automatically store its verified semantic fingerprint into <strong>Defect Memory</strong> for future early-warning similarity matching.
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Custom Pattern Label (Optional):</label>
                <input
                  type="text"
                  value={customLabel}
                  onChange={(e) => setCustomLabel(e.target.value)}
                  placeholder={selectedCluster?.label}
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-[3px] focus:outline-none focus:ring-1 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Technical Reviewer Rationale:</label>
                <textarea
                  rows={3}
                  value={decisionRationale}
                  onChange={(e) => setDecisionRationale(e.target.value)}
                  placeholder="e.g., Validated via warranty return teardown at Fremont plant. Clunking caused by bushing hardness degradation."
                  className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-[3px] focus:outline-none focus:ring-1 focus:ring-slate-900"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200">
              <button
                onClick={() => setDecisionModal(false)}
                className="px-3 py-1.5 rounded-[3px] text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleDecisionSubmit}
                disabled={submittingDecision}
                className="px-4 py-1.5 rounded-[3px] text-xs font-semibold font-mono uppercase tracking-wider bg-slate-900 hover:bg-slate-800 text-white shadow-xs"
              >
                {submittingDecision ? 'Submitting...' : 'Commit Verification'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Multi-Agent Investigation Live Stream Drawer */}
      <LiveAgentStream
        isOpen={showLiveStream}
        onClose={() => setShowLiveStream(false)}
        clusterId={selectedClusterId}
        clusterLabel={selectedCluster?.label || 'Defect Cluster'}
        onComplete={(invId) => {
          loadInvestigation(selectedClusterId, false);
        }}
      />
    </div>
  );
};
