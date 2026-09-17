import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal, 
  Activity, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Cpu, 
  FileText, 
  BookOpen, 
  X, 
  Play, 
  Pause, 
  ChevronRight, 
  Check, 
  Flame,
  Scale,
  Wrench,
  Search,
  Sparkles
} from 'lucide-react';
import { Report8D, TSBDraft } from '../types';

interface LiveAgentStreamProps {
  clusterId: string;
  clusterLabel: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (investigationId: string) => void;
}

interface StreamEventItem {
  id: string;
  time: string;
  event: string;
  role?: string;
  agent?: string;
  text: string;
  tool?: string;
  status?: string;
  duration_ms?: number;
  input?: any;
  confidence?: number;
  verdict?: string;
  details?: any;
}

interface StageProgress {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'running' | 'completed' | 'challenged';
  summary?: string;
}

const INITIAL_STAGES: StageProgress[] = [
  { id: 'investigator', name: 'Forensic Investigator', role: 'investigator', status: 'idle' },
  { id: 'analytics', name: 'Statistical Analytics', role: 'analytics', status: 'idle' },
  { id: 'red_team', name: 'Red Team Adversary', role: 'red_team', status: 'idle' },
  { id: 'regulatory', name: 'Regulatory & Safety', role: 'regulatory', status: 'idle' },
  { id: 'capa', name: 'CAPA Adjudicator', role: 'capa', status: 'idle' }
];

export const LiveAgentStream: React.FC<LiveAgentStreamProps> = ({
  clusterId,
  clusterLabel,
  isOpen,
  onClose,
  onComplete
}) => {
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [stages, setStages] = useState<StageProgress[]>(INITIAL_STAGES);
  const [events, setEvents] = useState<StreamEventItem[]>([]);
  const [activeTab, setActiveTab] = useState<'terminal' | 'debate' | '8d' | 'tsb'>('terminal');
  const [liveConfidence, setLiveConfidence] = useState<number>(0.85);
  const [completedInv, setCompletedInv] = useState<any | null>(null);
  const [report8D, setReport8D] = useState<Report8D | null>(null);
  const [tsbDraft, setTsbDraft] = useState<TSBDraft | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  
  const terminalEndRef = useRef<HTMLDivElement | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (isOpen && clusterId) {
      startStream(clusterId);
    }
    return () => {
      stopStream();
    };
  }, [isOpen, clusterId]);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const stopStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  const startStream = (cId: string) => {
    stopStream();
    setEvents([]);
    setStages(INITIAL_STAGES.map((s) => ({ ...s, status: 'idle' })));
    setCompletedInv(null);
    setReport8D(null);
    setTsbDraft(null);
    setStreamError(null);
    setIsStreaming(true);
    setLiveConfidence(0.85);

    const sseUrl = `/api/investigations/${cId}/stream`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    const addEvent = (item: Omit<StreamEventItem, 'id' | 'time'>) => {
      const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setEvents((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          time: timeStr,
          ...item
        }
      ]);
    };

    es.onopen = () => {
      addEvent({
        event: 'system',
        text: `Connected to Autonomous Investigation Mesh for cluster "${clusterLabel}" [ID: ${cId.substring(0, 8)}]`
      });
    };

    es.onmessage = (msgEvent) => {
      try {
        const payload = JSON.parse(msgEvent.data);
        const { event } = payload;

        if (event === 'stage_start') {
          const role = payload.role;
          setStages((prev) =>
            prev.map((s) => {
              if (s.role === role) return { ...s, status: 'running' };
              if (s.status === 'running') return { ...s, status: 'completed' };
              return s;
            })
          );
          addEvent({
            event: 'stage_start',
            role: payload.role,
            agent: payload.agent,
            text: `[STAGE INITIALIZED] ${payload.agent}: ${payload.description}`
          });
        } else if (event === 'agent_thought') {
          addEvent({
            event: 'agent_thought',
            role: payload.role,
            agent: payload.agent,
            text: `Thinking: ${payload.thought}`
          });
        } else if (event === 'tool_exec') {
          addEvent({
            event: 'tool_exec',
            role: payload.role,
            tool: payload.tool,
            status: payload.status,
            duration_ms: payload.duration_ms,
            input: payload.input,
            text: `Tool Executed [${payload.tool}] -> ${payload.output_summary || 'Completed'}`
          });
        } else if (event === 'finding') {
          addEvent({
            event: 'finding',
            role: payload.role,
            confidence: payload.confidence,
            text: `Finding [${payload.classification}]: ${payload.statement} (${payload.evidence_count} evidence claims)`
          });
        } else if (event === 'red_team_challenge') {
          setStages((prev) =>
            prev.map((s) => (s.role === 'red_team' ? { ...s, status: 'challenged' } : s))
          );
          if (payload.confidence_impact) {
            setLiveConfidence((prev) => Math.max(0.2, Number((prev + payload.confidence_impact).toFixed(2))));
          }
          addEvent({
            event: 'red_team_challenge',
            role: 'red_team',
            agent: 'Red Team Critic',
            verdict: payload.verdict,
            text: `Adversarial Check [${payload.check}]: ${payload.verdict} - ${payload.rationale}`
          });
        } else if (event === 'agent_event') {
          addEvent({
            event: 'agent_event',
            role: payload.role || 'agent',
            agent: payload.agent,
            text: payload.thought || payload.statement || JSON.stringify(payload)
          });
        } else if (event === 'complete') {
          setStages((prev) => prev.map((s) => ({ ...s, status: 'completed' })));
          setCompletedInv(payload);
          setLiveConfidence(payload.confidence);
          if (payload.report_8d) setReport8D(payload.report_8d);
          if (payload.tsb_draft) setTsbDraft(payload.tsb_draft);
          setIsStreaming(false);

          addEvent({
            event: 'complete',
            text: `Investigation concluded in ${payload.execution_time_ms}ms. Overall Verdict: ${payload.overall_classification} (Confidence: ${(payload.confidence * 100).toFixed(0)}%)`
          });

          es.close();
          if (onComplete) {
            onComplete(payload.investigation_id);
          }
        }
      } catch (err) {
        console.error('Error parsing SSE event', err);
      }
    };

    es.onerror = (err) => {
      console.error('SSE Stream error:', err);
      setStreamError('Stream disconnected or finished.');
      setIsStreaming(false);
      es.close();
    };
  };

  if (!isOpen) return null;

  const getRoleColor = (role?: string) => {
    switch (role) {
      case 'investigator':
        return 'text-sky-400 bg-sky-950/60 border-sky-800';
      case 'analytics':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800';
      case 'red_team':
        return 'text-rose-400 bg-rose-950/60 border-rose-800';
      case 'regulatory':
        return 'text-amber-400 bg-amber-950/60 border-amber-800';
      case 'capa':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 text-slate-100">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl h-[88vh] rounded-xl shadow-2xl flex flex-col overflow-hidden font-sans">
        {/* Header Bar */}
        <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="p-2 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <Cpu className="h-5 w-5" />
              </div>
              {isStreaming && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
                </span>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  Autonomous Multi-Agent Investigation Mesh
                </h2>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold border ${
                  isStreaming 
                    ? 'bg-emerald-950/70 text-emerald-300 border-emerald-700' 
                    : 'bg-slate-800 text-slate-300 border-slate-700'
                }`}>
                  {isStreaming ? 'LIVE STREAM ACTIVE' : 'CONCLUDED'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Cluster: <strong className="text-slate-200">{clusterLabel}</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Live Confidence Gauge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">Mesh Confidence:</span>
              <div className="flex items-center gap-1.5">
                <div className="w-16 bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${
                      liveConfidence >= 0.75 ? 'bg-emerald-500' : liveConfidence >= 0.5 ? 'bg-amber-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${Math.round(liveConfidence * 100)}%` }}
                  />
                </div>
                <span className="font-mono text-xs font-bold text-white">
                  {(liveConfidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* 5-Agent Pipeline Status Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-3 bg-slate-950/60 border-b border-slate-800 text-xs">
          {stages.map((st) => {
            const isRunning = st.status === 'running';
            const isDone = st.status === 'completed';
            const isChallenged = st.status === 'challenged';

            return (
              <div
                key={st.id}
                className={`p-2 rounded-md border transition-all flex flex-col justify-between space-y-1 ${
                  isRunning
                    ? 'bg-indigo-950/50 border-indigo-500/80 text-indigo-200 shadow-sm'
                    : isDone
                    ? 'bg-slate-900 border-slate-800 text-slate-300'
                    : isChallenged
                    ? 'bg-rose-950/30 border-rose-800/80 text-rose-300'
                    : 'bg-slate-950 border-slate-800/40 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[11px] truncate">{st.name}</span>
                  {isRunning ? (
                    <Activity className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
                  ) : isDone ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  ) : isChallenged ? (
                    <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                  ) : (
                    <Clock className="h-3.5 w-3.5 text-slate-600" />
                  )}
                </div>
                <div className="text-[10px] font-mono text-slate-400 capitalize">
                  {st.status}
                </div>
              </div>
            );
          })}
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center justify-between px-4 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-1 text-xs">
            <button
              onClick={() => setActiveTab('terminal')}
              className={`flex items-center gap-2 py-2.5 px-3 border-b-2 font-medium transition-colors ${
                activeTab === 'terminal'
                  ? 'border-indigo-500 text-white font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="h-3.5 w-3.5" />
              <span>Live Mesh Terminal ({events.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('debate')}
              className={`flex items-center gap-2 py-2.5 px-3 border-b-2 font-medium transition-colors ${
                activeTab === 'debate'
                  ? 'border-indigo-500 text-white font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Scale className="h-3.5 w-3.5" />
              <span>Dialectic Debate Log</span>
            </button>

            <button
              onClick={() => setActiveTab('8d')}
              className={`flex items-center gap-2 py-2.5 px-3 border-b-2 font-medium transition-colors ${
                activeTab === '8d'
                  ? 'border-indigo-500 text-white font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>8D Problem Solving Report</span>
              {report8D && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
            </button>

            <button
              onClick={() => setActiveTab('tsb')}
              className={`flex items-center gap-2 py-2.5 px-3 border-b-2 font-medium transition-colors ${
                activeTab === 'tsb'
                  ? 'border-indigo-500 text-white font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>TSB Service Bulletin Draft</span>
              {tsbDraft && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
            </button>
          </div>

          <div className="flex items-center gap-2 py-1">
            {!isStreaming && (
              <button
                onClick={() => startStream(clusterId)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <Play className="h-3 w-3" />
                <span>Re-stream Debate</span>
              </button>
            )}
          </div>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-950 font-mono text-xs text-slate-300">
          {/* TAB 1: Live Mesh Terminal */}
          {activeTab === 'terminal' && (
            <div className="space-y-2">
              {events.map((evt) => {
                const roleBadge = getRoleColor(evt.role);
                const isChallenge = evt.event === 'red_team_challenge';
                const isFinding = evt.event === 'finding';
                const isTool = evt.event === 'tool_exec';

                return (
                  <div
                    key={evt.id}
                    className={`p-2 rounded border text-xs leading-relaxed transition-all ${
                      isChallenge
                        ? 'bg-rose-950/40 border-rose-700/60 text-rose-200'
                        : isFinding
                        ? 'bg-indigo-950/30 border-indigo-700/50 text-indigo-100'
                        : isTool
                        ? 'bg-slate-900/80 border-slate-800 text-slate-300'
                        : 'bg-slate-950/60 border-slate-800/60 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-mono">{evt.time}</span>
                        {evt.role && (
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border uppercase ${roleBadge}`}>
                            {evt.agent || evt.role}
                          </span>
                        )}
                        {evt.tool && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-800 text-amber-300 border border-slate-700">
                            TOOL: {evt.tool}
                          </span>
                        )}
                        {evt.duration_ms !== undefined && (
                          <span className="text-[10px] text-slate-500 font-mono">
                            {evt.duration_ms}ms
                          </span>
                        )}
                      </div>

                      {evt.confidence !== undefined && (
                        <span className="text-[10px] font-mono text-emerald-400 font-bold">
                          Conf: {(evt.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    <div className="pl-1 font-sans text-xs">
                      {evt.text}
                    </div>

                    {evt.input && (
                      <div className="mt-1.5 p-1.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400 overflow-x-auto">
                        <span className="text-indigo-300 font-mono font-semibold">Params: </span>
                        {JSON.stringify(evt.input)}
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={terminalEndRef} />
            </div>
          )}

          {/* TAB 2: Dialectic Debate Log */}
          {activeTab === 'debate' && (
            <div className="space-y-4 font-sans">
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">
                <h3 className="font-bold text-white mb-1 flex items-center gap-2">
                  <Scale className="h-4 w-4 text-indigo-400" />
                  <span>Dialectic Multi-Agent Debate & Cross-Examination</span>
                </h3>
                <p className="text-slate-400 text-xs">
                  Agents generate testable hypotheses, query empirical fleet data via tools, and submit to Red Team adversarial challenge before CAPA adjudication.
                </p>
              </div>

              {/* Red Team Challenges Breakdown */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                  Adversarial Checks & Skepticism Log
                </h4>
                {events
                  .filter((e) => e.event === 'red_team_challenge')
                  .map((ch) => (
                    <div
                      key={ch.id}
                      className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/50 flex items-start gap-3 text-xs"
                    >
                      <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-rose-200">{ch.text.split(' - ')[0]}</span>
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono uppercase bg-rose-900/60 text-rose-300 border border-rose-700">
                            {ch.verdict || 'FLAGGED'}
                          </span>
                        </div>
                        <p className="text-rose-300/80">{ch.text.split(' - ')[1] || ch.text}</p>
                      </div>
                    </div>
                  ))}
                {events.filter((e) => e.event === 'red_team_challenge').length === 0 && (
                  <div className="p-4 rounded border border-slate-800 text-center text-slate-500 text-xs">
                    No active challenges logged yet. Start stream to watch live dialectic debate.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: 8D Report */}
          {activeTab === '8d' && (
            <div className="font-sans space-y-4">
              {report8D ? (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">
                        Standard 8D Problem Solving Dossier
                      </h3>
                      <p className="text-xs text-slate-400">
                        Generated by CAPA Adjudicator &bull; Cluster {clusterLabel}
                      </p>
                    </div>
                    <span className="px-2 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-mono font-bold">
                      ISO/TS 16949 Standard
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(report8D)
                      .filter(([k]) => k.startsWith('d') && typeof report8D[k as keyof Report8D] === 'object')
                      .map(([key, sec]: [string, any]) => (
                        <div key={key} className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                            <span className="font-mono text-xs font-bold text-indigo-400 uppercase">
                              {key.toUpperCase()} &bull; {sec.title}
                            </span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                              {sec.status || 'Verified'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                            {sec.content}
                          </p>
                        </div>
                      ))}
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs space-y-2">
                  <FileText className="h-8 w-8 mx-auto text-slate-600 animate-pulse" />
                  <p>8D problem solving synthesis pending completion of investigation stream.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: TSB Draft */}
          {activeTab === 'tsb' && (
            <div className="font-sans space-y-4">
              {tsbDraft ? (
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4 text-xs">
                  <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-indigo-400 font-bold tracking-wider">
                        Technical Service Bulletin (TSB) Draft
                      </span>
                      <h3 className="text-base font-bold text-white mt-0.5">{tsbDraft.title}</h3>
                    </div>
                    <span className="font-mono text-xs font-bold text-slate-300 bg-slate-800 px-2 py-1 rounded border border-slate-700">
                      TSB-{tsbDraft.tsb_id}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 font-semibold">Affected Vehicles:</span>
                      <p className="text-slate-200 mt-0.5">{tsbDraft.affected_vehicles}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold">Condition Description:</span>
                      <p className="text-slate-200 mt-0.5">{tsbDraft.condition}</p>
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-400 font-semibold">Diagnostic Procedure:</span>
                    <p className="text-slate-200 mt-1 whitespace-pre-wrap bg-slate-950 p-2.5 rounded border border-slate-800">
                      {tsbDraft.diagnostic_procedure}
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-400 font-semibold">Interim Repair Recommendation:</span>
                    <p className="text-slate-200 mt-1 whitespace-pre-wrap bg-slate-950 p-2.5 rounded border border-slate-800">
                      {tsbDraft.interim_repair_recommendation}
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-400 font-semibold">Warranty Coding Guidance:</span>
                    <p className="text-slate-300 mt-0.5 font-mono text-[11px]">{tsbDraft.warranty_coding_guidance}</p>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs space-y-2">
                  <BookOpen className="h-8 w-8 mx-auto text-slate-600 animate-pulse" />
                  <p>Technical Service Bulletin will be synthesized upon investigation completion.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Bar */}
        <div className="p-3.5 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-400 text-[11px] font-mono">
            <span>FastEmbed BGE-small &bull; SciPy Poisson Z-Score &bull; Dialectic ReAct Mesh</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              Close Live Stream
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
