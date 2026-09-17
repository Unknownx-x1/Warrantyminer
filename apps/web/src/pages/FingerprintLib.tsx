import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Search, 
  Sparkles, 
  CheckCircle2, 
  ShieldCheck, 
  ArrowRight,
  BookOpen,
  Info,
  RefreshCw,
  Layers,
  Activity,
  Tag,
  Scale,
  Wrench
} from 'lucide-react';
import { DefectFingerprint, MatchResult } from '../types';
import { api } from '../api/client';

const PRESET_QUERIES = [
  "Customer reports metallic clunking noise from front left wheel area when traversing speed bumps.",
  "Vehicle warning display shows turtle mode with low phase isolation error on power stage.",
  "Steering wheel vibrates violently under high-speed braking on freeway off-ramp.",
  "HVAC blower motor emits high-pitched grinding sound on fan speed 3."
];

export const FingerprintLib: React.FC = () => {
  const [fingerprints, setFingerprints] = useState<DefectFingerprint[]>([]);
  const [loading, setLoading] = useState(true);

  // Live Matcher State
  const [testNarrative, setTestNarrative] = useState(PRESET_QUERIES[0]);
  const [matching, setMatching] = useState(false);
  const [matchResults, setMatchResults] = useState<MatchResult[]>([]);

  useEffect(() => {
    loadFingerprints();
  }, []);

  const loadFingerprints = async () => {
    setLoading(true);
    try {
      const res = await api.getFingerprints();
      setFingerprints(res);
    } catch (err) {
      console.error('Failed to load fingerprints', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMatch = async (queryText?: string) => {
    const textToMatch = queryText || testNarrative;
    if (!textToMatch.trim()) return;
    setMatching(true);
    try {
      const results = await api.matchFingerprint({ narrative: textToMatch });
      setMatchResults(results);
    } catch (err) {
      console.error('Matching failed', err);
    } finally {
      setMatching(false);
    }
  };

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto text-slate-900">
      {/* Top Header & Educational Banner */}
      <div className="p-5 rounded-lg bg-white border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-indigo-50 text-indigo-700 border border-indigo-200">
              Institutional Neural Memory
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-slate-900 text-white">
              FastEmbed 384D Vector Space
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight font-sans">
              Defect Memory & Case-Based Reasoning (CBR)
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            When engineers confirm an emerging failure pattern, its 384-dimensional latent vector is preserved in Defect Memory to instantly triage future incoming dealership claims and prevent duplicate forensic investigations.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-700 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-md shadow-sm shrink-0">
          <Layers className="h-4 w-4 text-indigo-600" />
          <span>Active Defect Signatures: <strong className="text-indigo-700 font-bold">{fingerprints.length}</strong></span>
        </div>
      </div>

      {/* Live Semantic Matcher Console */}
      <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="text-[10px] font-mono uppercase text-indigo-700 font-bold tracking-wider block">
              Vectorized Cosine Similarity Search
            </span>
            <h3 className="text-sm font-bold text-slate-900 font-sans mt-0.5">
              Zero-Day Claim & Complaint Triage against Institutional Knowledge
            </h3>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
            <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
            <span>FastEmbed ONNX &bull; Unit Normalized Cosine Dot-Product</span>
          </div>
        </div>

        {/* Preset Sample Prompts */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-semibold text-slate-500 font-sans">Quick Test Presets:</span>
          {PRESET_QUERIES.map((preset, i) => (
            <button
              key={i}
              onClick={() => {
                setTestNarrative(preset);
                handleRunMatch(preset);
              }}
              className="text-[10px] font-mono bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 hover:border-indigo-300 rounded px-2 py-1 transition-colors truncate max-w-xs"
            >
              {preset.substring(0, 38)}...
            </button>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <textarea
            rows={2}
            value={testNarrative}
            onChange={(e) => setTestNarrative(e.target.value)}
            placeholder="Enter customer complaint or technician note to test match..."
            className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-md text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans leading-relaxed resize-none"
          />
          <button
            onClick={() => handleRunMatch()}
            disabled={matching}
            className="px-5 py-2.5 rounded-md text-xs font-bold font-sans bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 shadow-sm transition-colors self-end sm:self-auto h-auto flex items-center gap-2"
          >
            {matching ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Computing Cosine Vector...</span>
              </>
            ) : (
              <>
                <Search className="h-3.5 w-3.5" />
                <span>Match Defect Memory</span>
              </>
            )}
          </button>
        </div>

        {/* Live Match Results */}
        {matchResults.length > 0 && (
          <div className="pt-4 border-t border-slate-100 space-y-3">
            <span className="text-xs font-mono uppercase text-slate-700 block font-bold">
              Neural Vector Matches ({matchResults.length})
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {matchResults.map((match, idx) => {
                const isHigh = match.similarity_score >= 0.70;
                const isMed = match.similarity_score >= 0.50;

                return (
                  <div 
                    key={idx} 
                    className={`p-4 rounded-lg border space-y-2.5 font-sans transition-all ${
                      isHigh
                        ? 'bg-emerald-50/60 border-emerald-300 shadow-xs'
                        : isMed
                        ? 'bg-amber-50/60 border-amber-300 shadow-xs'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 font-sans">{match.fingerprint_name}</span>
                      <span className={`px-2 py-0.5 rounded font-mono text-[11px] font-bold border ${
                        isHigh
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : isMed
                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                          : 'bg-slate-200 text-slate-800 border-slate-300'
                      }`}>
                        {(match.similarity_score * 100).toFixed(1)}% Cosine Similarity
                      </span>
                    </div>
                    
                    {/* Visual Confidence Bar */}
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          isHigh ? 'bg-emerald-600' : isMed ? 'bg-amber-500' : 'bg-slate-500'
                        }`}
                        style={{ width: `${Math.min(100, match.similarity_score * 100)}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-600 font-sans">
                      <span>Target Component: <strong className="font-mono text-indigo-700">{match.component || '—'}</strong></span>
                      {match.confirmed_count && (
                        <span className="text-[10px] text-slate-500 font-mono">
                          Confirmed Cases: {match.confirmed_count}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed bg-white p-2.5 rounded border border-slate-200">
                      <strong className="text-slate-900 font-semibold">Diagnostic Recommendation: </strong> 
                      {match.recommendation}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Confirmed Defect Fingerprints Catalog */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 font-sans">
            Institutional Defect Catalog ({fingerprints.length})
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Confirmed failure signatures permanently archived into organizational neural memory.
          </p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 font-sans text-xs">
            Loading institutional defect memory...
          </div>
        ) : fingerprints.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-lg border border-slate-200 shadow-sm max-w-xl mx-auto space-y-2">
            <BookOpen className="h-8 w-8 text-slate-400 mx-auto" />
            <h4 className="text-sm font-bold text-slate-900">No Stored Defect Fingerprints</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              When reliability engineers confirm emerging defect clusters in the Investigation Console, their semantic failure signatures are permanently recorded here to automatically triage future incoming claims.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {fingerprints.map((fp) => (
              <div key={fp.id} className="p-5 rounded-lg border border-slate-200 bg-white shadow-sm space-y-3 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 font-sans">{fp.name}</h4>
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5 block font-semibold">
                      Component: {fp.component || 'Subsystem'}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 text-[10px] font-mono font-bold shrink-0">
                    CONFIRMED ({fp.confirmed_count || 1}x)
                  </span>
                </div>

                <div className="space-y-2.5 text-xs font-sans">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-500 block font-semibold">Recognized Symptoms</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {fp.symptoms.map((s, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-700 border border-slate-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  {fp.example_claims && fp.example_claims.length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                      <span className="text-[10px] font-mono uppercase text-slate-500 block font-semibold">Exemplar Field Citation</span>
                      <p className="text-xs text-slate-600 mt-1 italic line-clamp-3 leading-relaxed">
                        Claim {fp.example_claims[0]}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
