import React, { useState } from 'react';
import { 
  UploadCloud, 
  Database, 
  Play, 
  CheckCircle2, 
  Terminal,
  Clock,
  Layers,
  FileText,
  Info,
  Trash2
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisRunResponse } from '../types';

interface IngestionPageProps {
  onPipelineCompleted: () => void;
}

export const IngestionPage: React.FC<IngestionPageProps> = ({ onPipelineCompleted }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [uploadStats, setUploadStats] = useState<{ inserted: number; skipped: number; total: number } | null>(null);

  // Pipeline Execution State
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<AnalysisRunResponse | null>(null);
  const [logs, setLogs] = useState<string[]>([
    'System standby. Ready to ingest warranty claim records or execute surveillance pipeline.'
  ]);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, `[${timestamp}] ${msg}`]);
  };

  const handleResetDatabase = async () => {
    if (!window.confirm('Are you sure you want to remove all pre-seeded claims, clusters, and surveillance records from the database?')) {
      return;
    }
    setResetting(true);
    addLog('Initiating full database wipe & reset...');
    try {
      const res = await api.resetDatabase();
      addLog(res.message || 'Database wiped cleanly.');
      setUploadStats(null);
      setPipelineResult(null);
      onPipelineCompleted();
    } catch (err: any) {
      addLog(`Reset error: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const selected = e.target.files[0];
    setFile(selected);
    setUploading(true);
    addLog(`Uploading dataset: ${selected.name} (${(selected.size / 1024).toFixed(1)} KB)...`);

    try {
      const res = await api.uploadClaims(selected);
      setUploadStats({
        inserted: res.inserted,
        skipped: res.skipped_or_existing,
        total: res.inserted + res.skipped_or_existing
      });
      addLog(`Dataset ingested: ${res.inserted} claims inserted, ${res.skipped_or_existing} duplicate/existing records.`);
    } catch (err: any) {
      addLog(`Ingestion error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleRunPipeline = async () => {
    setRunningPipeline(true);
    addLog('Initiating end-to-end analytical surveillance pipeline...');
    
    try {
      const res = await api.runAnalysis({ force_recompute: true });
      setPipelineResult(res);

      if (res.events && res.events.length > 0) {
        res.events.forEach((ev) => addLog(ev));
      } else {
        addLog(`Surveillance run completed in ${res.processing_time_ms}ms.`);
        addLog(`Discovered ${res.clusters_found} semantic defect clusters (${res.alerts_high + res.alerts_critical} critical alerts).`);
      }
      onPipelineCompleted();
    } catch (err: any) {
      addLog(`Surveillance pipeline execution failed: ${err.message}`);
    } finally {
      setRunningPipeline(false);
    }
  };

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto text-slate-900">
      {/* Top Header & Educational Banner */}
      <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Data Operations
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight font-sans">
              Pipeline Execution & Telemetry Operations
            </h1>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
            Ingest raw automotive warranty datasets (CSV/JSON), trigger the end-to-end analytical pipeline (Extraction, Embeddings, HDBSCAN, Emergence Scoring), and inspect execution step timings.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleResetDatabase}
            disabled={resetting}
            className="flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-bold font-sans bg-white hover:bg-red-50 text-red-700 border border-red-200 hover:border-red-300 shadow-sm transition-all"
          >
            <Trash2 className="h-4 w-4 text-red-600" />
            <span>{resetting ? 'Wiping Database...' : 'Reset & Clear Database'}</span>
          </button>
        </div>
      </div>

      {/* 2-Column Operational Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Dataset Ingestion Card */}
        <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <span className="text-sm font-bold text-slate-900 font-sans">
                1. Upload Raw Claims Dataset
              </span>
              <span className="text-[11px] font-mono text-blue-700 font-semibold">CSV / JSON Multipart</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-sans">
              Upload raw warranty records exported from dealership dealer management systems (DMS) or quality databases.
            </p>

            <label className="border-2 border-dashed border-slate-200 hover:border-blue-500 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-50 text-center">
              <input
                type="file"
                accept=".csv,.json"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
              <FileText className="h-10 w-10 text-slate-400 mb-2" />
              <span className="text-xs font-bold text-slate-900 font-sans">
                {uploading ? 'Ingesting records into SQLite database...' : 'Select or drop warranty CSV/JSON file'}
              </span>
              <span className="text-[11px] text-slate-500 font-mono mt-1">
                Required columns: claim_id, date, model, plant, failure_code, narrative
              </span>
            </label>

            {uploadStats && (
              <div className="p-3 rounded-md bg-emerald-50 border border-emerald-200 text-xs font-mono space-y-1">
                <div className="flex justify-between text-slate-700">
                  <span>Inserted Records:</span>
                  <span className="text-emerald-800 font-bold">+{uploadStats.inserted} claims</span>
                </div>
                <div className="flex justify-between text-slate-700">
                  <span>Duplicate / Existing:</span>
                  <span className="text-slate-500">{uploadStats.skipped}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Pipeline Execution Controller */}
        <div className="p-6 rounded-lg border border-slate-200 bg-white shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <span className="text-sm font-bold text-slate-900 font-sans">
                2. Run Analytical Surveillance Engine
              </span>
              <span className="text-[11px] font-mono text-blue-700 font-semibold">HDBSCAN & Z-Score</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-sans">
              Executes the full surveillance cycle: narrative failure signature extraction, taxonomy contradiction analysis, dense semantic embeddings, unsupervised HDBSCAN clustering, and 5-factor emergence scoring.
            </p>

            {pipelineResult && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs pt-2">
                <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Run ID</span>
                  <span className="text-slate-900 font-bold mt-0.5 block truncate">{pipelineResult.run_id.split('-').slice(0, 2).join('-')}</span>
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Clusters</span>
                  <span className="text-slate-900 font-bold mt-0.5 block">{pipelineResult.clusters_found}</span>
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Alerts</span>
                  <span className="text-red-700 font-bold mt-0.5 block">{pipelineResult.alerts_high + pipelineResult.alerts_critical}</span>
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">Execution Latency</span>
                  <span className="text-slate-900 font-bold mt-0.5 block">{pipelineResult.processing_time_ms} ms</span>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={handleRunPipeline}
            disabled={runningPipeline}
            className={`w-full py-3 rounded-md text-xs font-bold font-mono uppercase tracking-wider transition-all flex items-center justify-center gap-2 shadow-sm ${
              runningPipeline
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                : 'bg-slate-900 hover:bg-slate-800 text-white active:scale-[0.98]'
            }`}
          >
            <Play className={`h-4 w-4 ${runningPipeline ? 'animate-spin' : ''}`} />
            <span>{runningPipeline ? 'Executing Surveillance Pipeline...' : 'Execute Full Pipeline'}</span>
          </button>
        </div>
      </div>

      {/* Live Pipeline Telemetry Terminal */}
      <div className="p-5 rounded-lg border border-slate-200 bg-white shadow-sm space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-800 font-mono">
            <Terminal className="h-4 w-4 text-blue-600" />
            <span>Execution Telemetry Event Stream</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Real-Time Backend Log</span>
        </div>

        <div className="p-4 bg-slate-950 text-slate-200 rounded-md font-mono text-xs max-h-56 overflow-y-auto space-y-1.5 border border-slate-800 shadow-inner">
          {logs.map((log, idx) => (
            <div key={idx} className="leading-relaxed">
              <span className="text-blue-400 select-none mr-2">&gt;</span>
              <span>{log}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
