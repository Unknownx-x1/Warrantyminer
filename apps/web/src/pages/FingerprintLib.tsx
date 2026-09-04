import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Search, 
  Sparkles, 
  CheckCircle2, 
  ShieldCheck, 
  ArrowRight,
  BookOpen,
  Info
} from 'lucide-react';
import { DefectFingerprint, MatchResult } from '../types';
import { api } from '../api/client';

export const FingerprintLib: React.FC = () => {
  const [fingerprints, setFingerprints] = useState<DefectFingerprint[]>([]);
  const [loading, setLoading] = useState(true);

  // Live Matcher State
  const [testNarrative, setTestNarrative] = useState('Customer reports metallic clunking noise from front left wheel area when going over speed bumps.');
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

  const handleRunMatch = async () => {
    if (!testNarrative.trim()) return;
    setMatching(true);
    try {
      const results = await api.matchFingerprint({ narrative: testNarrative });
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
      <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Institutional Knowledge
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight font-sans">
              Defect Memory & Institutional Knowledge Base
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            When engineers confirm an emerging failure pattern, its semantic signature is retained in Defect Memory to instantly triage future incoming dealership complaints and prevent duplicate investigations.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-700 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-md shadow-sm shrink-0">
          <span>Active Defect Signatures: <strong className="text-blue-700">{fingerprints.length}</strong></span>
        </div>
      </div>

      {/* Live Semantic Matcher Console */}
      <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4">
        <div>
          <span className="text-[10px] font-mono uppercase text-blue-700 font-bold tracking-wider block">
            Automated Semantic Matcher
          </span>
          <h3 className="text-sm font-bold text-slate-900 font-sans mt-0.5">
            Test Incoming Customer Complaints Against Defect Memory
          </h3>
          <p className="text-xs text-slate-500 mt-0.5 font-sans">
            Type any customer complaint or technician note below to compute dense cosine similarity against institutional defect fingerprints.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <textarea
            rows={2}
            value={testNarrative}
            onChange={(e) => setTestNarrative(e.target.value)}
            placeholder="Enter customer complaint or technician note to test match..."
            className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans leading-relaxed resize-none"
          />
          <button
            onClick={handleRunMatch}
            disabled={matching}
            className="px-5 py-2.5 rounded-md text-xs font-bold font-sans bg-slate-900 hover:bg-slate-800 text-white shrink-0 shadow-sm transition-colors self-end sm:self-auto h-auto"
          >
            {matching ? 'Computing Cosine Match...' : 'Match Defect Memory'}
          </button>
        </div>

        {/* Live Match Results */}
        {matchResults.length > 0 && (
          <div className="pt-4 border-t border-slate-100 space-y-3">
            <span className="text-xs font-mono uppercase text-slate-700 block font-bold">
              Cosine Similarity Matches ({matchResults.length})
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {matchResults.map((match, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-emerald-50/50 border border-emerald-200 space-y-2.5 font-sans">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 font-sans">{match.fingerprint_name}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-mono text-[11px] font-bold">
                      {(match.similarity_score * 100).toFixed(1)}% Match Confidence
                    </span>
                  </div>
                  
                  {/* Visual Confidence Bar */}
                  <div className="w-full bg-emerald-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-600 h-full rounded-full" style={{ width: `${Math.min(100, match.similarity_score * 100)}%` }}></div>
                  </div>

                  <p className="text-xs text-slate-600">
                    Target Component: <span className="font-mono text-blue-700 font-bold">{match.component || '—'}</span>
                  </p>
                  <p className="text-xs text-slate-700 leading-relaxed bg-white p-2.5 rounded border border-emerald-200">
                    <strong className="text-emerald-900">Diagnostic Recommendation:</strong> {match.recommendation}
                  </p>
                </div>
              ))}
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
            Confirmed failure signatures permanently archived into organizational memory.
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
                    CONFIRMED
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
                      <span className="text-[10px] font-mono uppercase text-slate-500 block font-semibold">Exemplar Field Narrative</span>
                      <p className="text-xs text-slate-600 mt-1 italic line-clamp-3 leading-relaxed">
                        "{fp.example_claims[0]}"
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
