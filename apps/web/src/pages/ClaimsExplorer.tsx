import React, { useState, useEffect } from 'react';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Flame, 
  XCircle,
  FileText,
  Filter,
  Info
} from 'lucide-react';
import { Claim, ClaimsListResponse } from '../types';
import { api } from '../api/client';

export const ClaimsExplorer: React.FC = () => {
  const [claimsData, setClaimsData] = useState<ClaimsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCode, setSelectedCode] = useState('');
  const [selectedPlant, setSelectedPlant] = useState('');
  const [mismatchOnly, setMismatchOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);

  useEffect(() => {
    loadClaims();
  }, [page, selectedCode, selectedPlant, mismatchOnly]);

  const loadClaims = async () => {
    setLoading(true);
    try {
      const res = await api.getClaims({
        search: searchTerm || undefined,
        failure_code: selectedCode || undefined,
        plant: selectedPlant || undefined,
        mismatch_only: mismatchOnly,
        page,
        page_size: 25
      });
      setClaimsData(res);
    } catch (err) {
      console.error('Failed to load claims', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadClaims();
  };

  const totalPages = claimsData ? Math.ceil(claimsData.total / claimsData.page_size) : 1;

  return (
    <div className="space-y-5 max-w-[1440px] mx-auto text-slate-900">
      {/* Top Header & Educational Banner */}
      <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Raw Telemetry Explorer
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight font-sans">
              Claims & Diagnostic Narratives Explorer
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            Search raw dealership warranty records, inspect AI-extracted failure modes, and identify <span className="font-semibold text-amber-800">Taxonomy Mismatches</span> where assigned codes contradicted technician observations.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => { setMismatchOnly(!mismatchOnly); setPage(1); }}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-bold font-sans transition-all shadow-sm ${
              mismatchOnly
                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300'
            }`}
          >
            <Flame className="h-4 w-4 text-amber-600" />
            <span>{mismatchOnly ? 'Showing Mismatches Only' : 'Filter by Mismatches Only'}</span>
          </button>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex flex-col md:flex-row items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search narrative text, symptoms, or Claim ID (e.g. C-9001, clunking, bushing)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans"
          />
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={selectedCode}
            onChange={(e) => { setSelectedCode(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-700 font-mono focus:outline-none focus:border-blue-500"
          >
            <option value="">All Failure Codes</option>
            <option value="OTHER">OTHER</option>
            <option value="RIDE QUALITY">RIDE QUALITY</option>
            <option value="SUSPENSION">SUSPENSION</option>
            <option value="ELECTRICAL-NFF">ELECTRICAL-NFF</option>
            <option value="STEERING">STEERING</option>
            <option value="HVAC">HVAC</option>
            <option value="BRAKES">BRAKES</option>
            <option value="POWERTRAIN">POWERTRAIN</option>
          </select>

          <select
            value={selectedPlant}
            onChange={(e) => { setSelectedPlant(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-700 font-sans focus:outline-none focus:border-blue-500"
          >
            <option value="">All Facilities</option>
            <option value="Plant A - Fremont">Plant A - Fremont</option>
            <option value="Plant B - Austin">Plant B - Austin</option>
            <option value="Plant C - Leipzig">Plant C - Leipzig</option>
          </select>
        </div>
      </div>

      {/* Dense Claims Table */}
      <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-mono border-b border-slate-200 tracking-wider">
              <tr>
                <th className="py-3 px-3">Claim ID</th>
                <th className="py-3 px-3">Date</th>
                <th className="py-3 px-3">Model</th>
                <th className="py-3 px-3">Plant</th>
                <th className="py-3 px-3">Assigned Code</th>
                <th className="py-3 px-3">AI Inferred Failure</th>
                <th className="py-3 px-3">Mismatch</th>
                <th className="py-3 px-4">Technician Narrative</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 font-sans text-xs">
                    Loading warranty claim telemetry...
                  </td>
                </tr>
              ) : !claimsData || claimsData.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 font-sans text-xs">
                    No warranty claims matched your search parameters.
                  </td>
                </tr>
              ) : (
                claimsData.items.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => setSelectedClaim(c)}
                    className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 text-blue-700 font-bold">
                      {c.external_claim_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {c.claim_date}
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 font-sans text-[11px]">
                      {c.product_model || '—'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {c.plant ? c.plant.split(' - ')[0] : '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 text-[10px] font-semibold">
                        {c.failure_code || 'UNASSIGNED'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-800 font-sans text-[11px] max-w-xs truncate">
                      {c.signature?.inferred_failure || '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      {c.mismatch ? (
                        <span className="px-2 py-0.5 rounded bg-red-100 text-red-800 border border-red-200 text-[10px] font-bold">
                          MISMATCH
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px]">MATCH</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-600 font-sans text-xs max-w-lg truncate">
                      {c.narrative}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {claimsData && (
          <div className="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>
              Showing {((page - 1) * claimsData.page_size) + 1}–{Math.min(page * claimsData.page_size, claimsData.total)} of {claimsData.total.toLocaleString()} claims
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded bg-white border border-slate-300 text-slate-600 hover:text-slate-900 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="px-2 font-bold text-slate-900">
                {page} / {totalPages || 1}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded bg-white border border-slate-300 text-slate-600 hover:text-slate-900 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
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

            {selectedClaim.signature && (
              <div className="p-3.5 rounded bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-[10px] font-mono uppercase text-blue-700 block font-bold">AI Extracted Semantic Signature</span>
                <div className="grid grid-cols-3 gap-2 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Component</span>
                    <span className="text-slate-900 block font-semibold">{selectedClaim.signature.component || '—'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Symptom</span>
                    <span className="text-slate-900 block font-semibold">{selectedClaim.signature.symptom || '—'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Inferred Defect</span>
                    <span className="text-blue-700 font-bold block">{selectedClaim.signature.inferred_failure || '—'}</span>
                  </div>
                </div>
              </div>
            )}

            {selectedClaim.mismatch && (
              <div className="p-3.5 rounded bg-red-50 border border-red-200 space-y-1">
                <span className="text-[10px] font-mono uppercase text-red-700 block font-bold">Taxonomy Mismatch Analysis</span>
                <p className="text-xs text-red-800 font-sans">{selectedClaim.mismatch.reason || 'Structured failure code contradicts extracted narrative defect.'}</p>
              </div>
            )}

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
    </div>
  );
};
