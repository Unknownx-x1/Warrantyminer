import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { CommandCenter } from './pages/CommandCenter';
import { PatternDetail } from './pages/PatternDetail';
import { BaselineCompare } from './pages/BaselineCompare';
import { ClaimsExplorer } from './pages/ClaimsExplorer';
import { FingerprintLib } from './pages/FingerprintLib';
import { IngestionPage } from './pages/IngestionPage';
import { DashboardSummary, ClusterListItem } from './types';
import { api } from './api/client';

export function App() {
  const [activeTab, setActiveTab] = useState('command-center');
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  // Global State
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [clusters, setClusters] = useState<ClusterListItem[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);

  useEffect(() => {
    loadGlobalData();
  }, []);

  const loadGlobalData = async () => {
    try {
      const summaryData = await api.getSummary();
      setSummary(summaryData);

      const clustersData = await api.getClusters();
      setClusters(clustersData);
    } catch (err) {
      console.error('Failed to fetch initial dashboard state', err);
    } finally {
      setLoadingInitial(false);
    }
  };

  const handleRunPipeline = async () => {
    setIsAnalyzing(true);
    try {
      await api.runAnalysis({ force_recompute: true });
      await loadGlobalData();
    } catch (err: any) {
      alert(`Pipeline error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectCluster = (clusterId: string) => {
    setSelectedClusterId(clusterId);
    setActiveTab('investigation');
  };

  return (
    <div className="min-h-screen bg-[#f4f6f9] text-slate-900 flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
        }}
        onRunPipeline={handleRunPipeline}
        isAnalyzing={isAnalyzing}
      />

      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 py-5">
        {loadingInitial ? (
          <div className="py-32 text-center">
            <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-3 text-xs font-mono text-slate-500">Connecting to WarrantyPatternMiner Surveillance Engine...</p>
          </div>
        ) : (
          <>
            {activeTab === 'command-center' && (
              <CommandCenter
                summary={summary}
                clusters={clusters}
                onSelectCluster={handleSelectCluster}
                onNavigateToComparison={() => setActiveTab('comparison')}
                onRunPipeline={handleRunPipeline}
                isAnalyzing={isAnalyzing}
              />
            )}

            {activeTab === 'investigation' && (
              <PatternDetail
                clusterId={selectedClusterId || (clusters[0]?.id || '')}
                onBack={() => setActiveTab('command-center')}
                onRefreshSummary={loadGlobalData}
              />
            )}

            {activeTab === 'comparison' && (
              <BaselineCompare
                onSelectCluster={handleSelectCluster}
              />
            )}

            {activeTab === 'claims' && (
              <ClaimsExplorer />
            )}

            {activeTab === 'fingerprints' && (
              <FingerprintLib />
            )}

            {activeTab === 'pipeline' && (
              <IngestionPage
                onPipelineCompleted={loadGlobalData}
              />
            )}
          </>
        )}
      </main>

      {/* Industrial Telemetry Footer */}
      <footer className="border-t border-slate-200 bg-white py-3 text-xs font-mono text-slate-500">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>WarrantyPatternMiner v2.0 • Field Defect Early Warning Surveillance Platform</span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Database: SQLite Active • Engine: HDBSCAN / Z-Score / CUSUM
          </span>
        </div>
      </footer>
    </div>
  );
}
