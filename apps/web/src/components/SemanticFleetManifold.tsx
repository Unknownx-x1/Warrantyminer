import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Layers, 
  Sparkles, 
  Search, 
  Filter, 
  AlertTriangle, 
  ShieldAlert, 
  RefreshCw, 
  Maximize2, 
  Info, 
  Compass, 
  Tag, 
  ChevronRight,
  Eye,
  Activity
} from 'lucide-react';
import { api } from '../api/client';
import { SemanticManifoldData, ManifoldPoint, ManifoldCluster } from '../types';
import { Badge } from './common/Badge';

interface SemanticFleetManifoldProps {
  onSelectCluster?: (clusterId: string) => void;
  onSelectClaim?: (claimId: string) => void;
  selectedClusterId?: string | null;
}

const CLUSTER_COLORS: Record<string, { bg: string; stroke: string; fill: string; text: string }> = {
  CRITICAL: { bg: 'rgba(239, 68, 68, 0.12)', stroke: '#ef4444', fill: '#dc2626', text: 'text-red-700' },
  HIGH: { bg: 'rgba(249, 115, 22, 0.12)', stroke: '#f97316', fill: '#ea580c', text: 'text-orange-700' },
  WATCH: { bg: 'rgba(234, 179, 8, 0.12)', stroke: '#eab308', fill: '#ca8a04', text: 'text-amber-800' },
  NORMAL: { bg: 'rgba(59, 130, 246, 0.10)', stroke: '#3b82f6', fill: '#2563eb', text: 'text-blue-700' }
};

export const SemanticFleetManifold: React.FC<SemanticFleetManifoldProps> = ({
  onSelectCluster,
  onSelectClaim,
  selectedClusterId
}) => {
  const [manifoldData, setManifoldData] = useState<SemanticManifoldData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [method, setMethod] = useState<'umap' | 'pca'>('umap');
  const [filterCluster, setFilterCluster] = useState<string>('ALL');
  const [filterAlert, setFilterAlert] = useState<string>('ALL');
  const [highlightMismatches, setHighlightMismatches] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [hoveredPoint, setHoveredPoint] = useState<ManifoldPoint | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<ManifoldPoint | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    loadManifold(method);
  }, [method]);

  useEffect(() => {
    if (selectedClusterId && selectedClusterId !== filterCluster) {
      setFilterCluster(selectedClusterId);
    }
  }, [selectedClusterId]);

  const loadManifold = async (m: 'umap' | 'pca') => {
    try {
      setLoading(true);
      const data = await api.getSemanticManifold(m);
      setManifoldData(data);
    } catch (err) {
      console.error('Failed to load semantic manifold:', err);
    } finally {
      setLoading(false);
    }
  };

  // Dimensions of the coordinate plane
  const width = 900;
  const height = 580;
  const padding = 45;

  // Transform normalized [-90, 90] to SVG [padding, width - padding]
  const scaleX = (x: number) => padding + ((x + 90) / 180) * (width - 2 * padding);
  const scaleY = (y: number) => padding + ((-y + 90) / 180) * (height - 2 * padding);

  // Filtered Points
  const filteredPoints = useMemo(() => {
    if (!manifoldData) return [];
    return manifoldData.points.filter((pt) => {
      if (filterCluster !== 'ALL' && pt.cluster_id !== filterCluster) {
        return false;
      }
      if (filterAlert !== 'ALL') {
        const cluster = manifoldData.clusters.find((c) => c.cluster_id === pt.cluster_id);
        if (!cluster || cluster.alert_level !== filterAlert) return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchClaim = pt.external_id.toLowerCase().includes(q);
        const matchNarrative = pt.narrative.toLowerCase().includes(q);
        const matchComp = pt.component.toLowerCase().includes(q);
        const matchCode = pt.failure_code.toLowerCase().includes(q);
        if (!matchClaim && !matchNarrative && !matchComp && !matchCode) return false;
      }
      return true;
    });
  }, [manifoldData, filterCluster, filterAlert, searchQuery]);

  // Filtered Clusters
  const filteredClusters = useMemo(() => {
    if (!manifoldData) return [];
    if (filterCluster !== 'ALL') {
      return manifoldData.clusters.filter((c) => c.cluster_id === filterCluster);
    }
    if (filterAlert !== 'ALL') {
      return manifoldData.clusters.filter((c) => c.alert_level === filterAlert);
    }
    return manifoldData.clusters;
  }, [manifoldData, filterCluster, filterAlert]);

  const handlePointHover = (pt: ManifoldPoint | null, e?: React.MouseEvent) => {
    setHoveredPoint(pt);
    if (pt && e && svgRef.current) {
      const rect = svgRef.current.getBoundingClientRect();
      setTooltipPos({
        x: e.clientX - rect.left + 15,
        y: e.clientY - rect.top - 15
      });
    } else if (!pt) {
      setTooltipPos(null);
    }
  };

  const handlePointClick = (pt: ManifoldPoint) => {
    setSelectedPoint(pt);
    if (onSelectClaim) {
      onSelectClaim(pt.claim_id);
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-lg shadow-sm overflow-hidden text-slate-900">
      {/* Header */}
      <div className="p-4 bg-slate-900 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold font-sans tracking-tight text-slate-100">
                Fleet Semantic Manifold Projection (2D Neural Embedding Space)
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-indigo-900/60 text-indigo-300 border border-indigo-700/60 font-semibold">
                FastEmbed 384D &rarr; {method.toUpperCase()} 2D
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuously maps technician narratives into latent topology. Clusters delineate emerging defects; highlighted markers indicate code contradictions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Method Selector */}
          <div className="flex items-center rounded-md bg-slate-800 p-0.5 border border-slate-700 text-xs font-mono">
            <button
              onClick={() => setMethod('umap')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                method === 'umap'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              UMAP (Cosine)
            </button>
            <button
              onClick={() => setMethod('pca')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                method === 'pca'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              PCA (Linear)
            </button>
          </div>

          <button
            onClick={() => loadManifold(method)}
            disabled={loading}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            title="Reload Projection"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter & Control Ribbon */}
      <div className="p-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search */}
          <div className="relative w-56">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search narrative, code, VIN..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-2.5 py-1.5 rounded border border-slate-300 bg-white text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Cluster Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-600">Cluster:</span>
            <select
              value={filterCluster}
              onChange={(e) => setFilterCluster(e.target.value)}
              className="px-2 py-1.5 rounded border border-slate-300 bg-white text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Clusters ({manifoldData?.clusters.length || 0})</option>
              {manifoldData?.clusters.map((c) => (
                <option key={c.cluster_id} value={c.cluster_id}>
                  [{c.alert_level}] {c.label.substring(0, 32)} ({c.claim_count} claims)
                </option>
              ))}
            </select>
          </div>

          {/* Alert Level Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-600">Risk:</span>
            <select
              value={filterAlert}
              onChange={(e) => setFilterAlert(e.target.value)}
              className="px-2 py-1.5 rounded border border-slate-300 bg-white text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Alert Levels</option>
              <option value="CRITICAL">CRITICAL (&ge;80)</option>
              <option value="HIGH">HIGH (60-79)</option>
              <option value="WATCH">WATCH (40-59)</option>
              <option value="NORMAL">NORMAL (&lt;40)</option>
            </select>
          </div>

          {/* Mismatch Highlight Toggle */}
          <button
            onClick={() => setHighlightMismatches(!highlightMismatches)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded border transition-colors ${
              highlightMismatches
                ? 'bg-amber-50 text-amber-900 border-amber-300 font-semibold'
                : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
            }`}
          >
            <AlertTriangle className={`h-3.5 w-3.5 ${highlightMismatches ? 'text-amber-600' : 'text-slate-400'}`} />
            <span>Highlight Code Mismatches</span>
          </button>
        </div>

        {/* Live Counters */}
        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-600">
          <div>
            Showing <strong className="text-slate-900">{filteredPoints.length}</strong> / {manifoldData?.total_points || 0} claims
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1 text-red-700 font-semibold">
            <span className="w-2 h-2 rounded-full bg-red-600 inline-block" />
            <span>{manifoldData?.clusters.filter((c) => c.alert_level === 'CRITICAL').length || 0} Critical Clusters</span>
          </div>
        </div>
      </div>

      {/* Main Visualizer Area */}
      <div className="relative bg-slate-950 flex flex-col items-center justify-center p-2 select-none overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-30 flex flex-col items-center justify-center text-slate-200 space-y-2">
            <RefreshCw className="h-7 w-7 animate-spin text-indigo-400" />
            <span className="text-xs font-mono tracking-wide">Computing FastEmbed Dimensionality Reduction ({method.toUpperCase()})...</span>
          </div>
        )}

        <div className="relative w-full max-w-[920px] aspect-[900/580] bg-slate-950 rounded border border-slate-800 shadow-inner overflow-hidden">
          {/* Subtle Grid Lines */}
          <svg
            ref={svgRef}
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-full cursor-crosshair"
            onMouseLeave={() => handlePointHover(null)}
          >
            <defs>
              <radialGradient id="criticalGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
              </radialGradient>
              <radialGradient id="highGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#f97316" stopOpacity="0.0" />
              </radialGradient>
              <pattern id="gridPattern" width="45" height="45" patternUnits="userSpaceOnUse">
                <path d="M 45 0 L 0 0 0 45" fill="none" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2 4" />
              </pattern>
            </defs>

            {/* Background Grid */}
            <rect width={width} height={height} fill="url(#gridPattern)" />

            {/* Axis Crosshairs */}
            <line x1={width / 2} y1={padding} x2={width / 2} y2={height - padding} stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />
            <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />

            <text x={width - padding + 5} y={height / 2 + 3} fill="#64748b" fontSize="9" fontFamily="monospace">
              Component Semantics (Dim 1)
            </text>
            <text x={width / 2 + 5} y={padding - 10} fill="#64748b" fontSize="9" fontFamily="monospace">
              Symptom Severity (Dim 2)
            </text>

            {/* Cluster Convex Hulls (Background Polygons) */}
            {filteredClusters.map((cluster) => {
              if (!cluster.hull || cluster.hull.length < 3) return null;
              const pointsStr = cluster.hull
                .map(([hx, hy]) => `${scaleX(hx)},${scaleY(hy)}`)
                .join(' ');
              const colors = CLUSTER_COLORS[cluster.alert_level] || CLUSTER_COLORS.NORMAL;
              const isSelected = selectedClusterId === cluster.cluster_id || filterCluster === cluster.cluster_id;

              return (
                <g key={`hull-${cluster.cluster_id}`}>
                  <polygon
                    points={pointsStr}
                    fill={colors.bg}
                    stroke={colors.stroke}
                    strokeWidth={isSelected ? 2.5 : 1.2}
                    strokeDasharray={cluster.alert_level === 'CRITICAL' ? 'none' : '4 2'}
                    className="transition-all duration-200 cursor-pointer hover:fill-opacity-50"
                    onClick={() => {
                      if (onSelectCluster) onSelectCluster(cluster.cluster_id);
                      setFilterCluster(cluster.cluster_id);
                    }}
                  />
                  {/* Centroid Label */}
                  <g
                    transform={`translate(${scaleX(cluster.centroid.x)}, ${scaleY(cluster.centroid.y)})`}
                    className="cursor-pointer"
                    onClick={() => {
                      if (onSelectCluster) onSelectCluster(cluster.cluster_id);
                      setFilterCluster(cluster.cluster_id);
                    }}
                  >
                    <rect
                      x="-60"
                      y="-11"
                      width="120"
                      height="20"
                      rx="3"
                      fill="#0f172a"
                      stroke={colors.stroke}
                      strokeWidth="1"
                      fillOpacity="0.9"
                    />
                    <text
                      x="0"
                      y="3"
                      textAnchor="middle"
                      fill="#f8fafc"
                      fontSize="9.5"
                      fontFamily="sans-serif"
                      fontWeight="bold"
                    >
                      {cluster.label.length > 18 ? cluster.label.substring(0, 16) + '...' : cluster.label}
                    </text>
                  </g>
                </g>
              );
            })}

            {/* Data Points */}
            {filteredPoints.map((pt) => {
              const cx = scaleX(pt.x);
              const cy = scaleY(pt.y);
              const cluster = manifoldData?.clusters.find((c) => c.cluster_id === pt.cluster_id);
              const alertLevel = cluster?.alert_level || 'NORMAL';
              const isNoise = pt.is_noise;
              const isMismatch = pt.is_mismatch === 1;
              const isHovered = hoveredPoint?.claim_id === pt.claim_id;
              const isSelected = selectedPoint?.claim_id === pt.claim_id;

              let fillColor = '#64748b'; // default slate-500
              let radius = 3.5;

              if (!isNoise) {
                if (alertLevel === 'CRITICAL') fillColor = '#ef4444';
                else if (alertLevel === 'HIGH') fillColor = '#f97316';
                else if (alertLevel === 'WATCH') fillColor = '#eab308';
                else fillColor = '#38bdf8';
                radius = 4.2;
              }

              if (isMismatch && highlightMismatches) {
                fillColor = '#fbbf24'; // luminous amber
                radius = 5.0;
              }

              if (isHovered || isSelected) {
                radius = 7.0;
              }

              return (
                <g key={pt.claim_id} className="cursor-pointer">
                  {/* Pulsing Aura for Mismatches & Critical */}
                  {(isMismatch && highlightMismatches) && (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={radius + 4}
                      fill="none"
                      stroke="#f59e0b"
                      strokeWidth="1.2"
                      strokeDasharray="2 2"
                      opacity="0.8"
                    />
                  )}

                  <circle
                    cx={cx}
                    cy={cy}
                    r={radius}
                    fill={fillColor}
                    stroke={isHovered || isSelected ? '#ffffff' : isMismatch ? '#d97706' : '#0f172a'}
                    strokeWidth={isHovered || isSelected ? 2 : 1}
                    className="transition-all duration-100"
                    onMouseEnter={(e) => handlePointHover(pt, e)}
                    onClick={() => handlePointClick(pt)}
                  />
                </g>
              );
            })}
          </svg>

          {/* Interactive Floating Hover Tooltip */}
          {hoveredPoint && tooltipPos && (
            <div
              className="absolute z-40 bg-slate-900/95 border border-slate-700 text-slate-100 p-3 rounded-md shadow-2xl backdrop-blur-md pointer-events-none max-w-sm"
              style={{
                left: Math.min(tooltipPos.x, width - 280),
                top: Math.min(tooltipPos.y, height - 180)
              }}
            >
              <div className="flex items-center justify-between gap-2 border-b border-slate-700/80 pb-1.5 mb-1.5">
                <span className="font-mono text-xs font-bold text-indigo-300">
                  {hoveredPoint.external_id}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {hoveredPoint.date || 'Unknown Date'}
                </span>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Assigned Code:</span>
                  <span className="font-mono font-bold text-slate-200">{hoveredPoint.failure_code}</span>
                </div>

                {hoveredPoint.is_mismatch === 1 && (
                  <div className="p-1 rounded bg-amber-950/60 border border-amber-600/50 text-amber-300 text-[10px] flex items-center gap-1 font-semibold">
                    <AlertTriangle className="h-3 w-3 text-amber-400 shrink-0" />
                    <span>Neural Contradiction ({hoveredPoint.mismatch_severity})</span>
                  </div>
                )}

                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Component / Symptom:</span>
                  <span className="text-slate-200 font-semibold">{hoveredPoint.component} &bull; {hoveredPoint.symptom}</span>
                </div>

                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Plant / Model:</span>
                  <span className="text-slate-300">{hoveredPoint.plant} &bull; {hoveredPoint.model}</span>
                </div>

                <div className="text-[11px] text-slate-300 italic pt-1 line-clamp-2 border-t border-slate-800 mt-1">
                  &ldquo;{hoveredPoint.narrative}&rdquo;
                </div>

                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400">
                  <span>Cluster: <strong className="text-slate-200">{hoveredPoint.cluster_label}</strong></span>
                  <span className="text-indigo-400 font-semibold">Click to inspect</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Legend Ribbon */}
        <div className="w-full max-w-[920px] mt-2 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400 px-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
              <span>Critical Defect</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block" />
              <span>High Alert</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
              <span>Watch List</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block" />
              <span>Normal Pattern</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block" />
              <span>Noise (Isolated)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full border border-amber-400 bg-amber-400/30 inline-block" />
              <span className="text-amber-300 font-semibold">Code Mismatch</span>
            </div>
          </div>

          <div className="text-[10px] font-mono text-slate-500">
            Convex hulls computed via SciPy QHull &bull; Real-time Cosine Topography
          </div>
        </div>
      </div>

      {/* Selected Point Bottom Drawer */}
      {selectedPoint && (
        <div className="p-3.5 bg-slate-900 border-t border-slate-800 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="space-y-1 max-w-3xl">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-xs text-indigo-300">{selectedPoint.external_id}</span>
              <span className="text-slate-500">&bull;</span>
              <span className="text-xs text-slate-300 font-semibold">Code: {selectedPoint.failure_code}</span>
              {selectedPoint.is_mismatch === 1 && (
                <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-900/60 text-amber-300 border border-amber-700 font-mono">
                  MISCODED ({selectedPoint.mismatch_severity})
                </span>
              )}
              <span className="text-slate-500">&bull;</span>
              <span className="text-xs text-slate-300">{selectedPoint.plant} &bull; {selectedPoint.model}</span>
            </div>
            <p className="text-xs text-slate-300 leading-snug">
              &ldquo;{selectedPoint.narrative}&rdquo;
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {selectedPoint.cluster_id && onSelectCluster && (
              <button
                onClick={() => onSelectCluster(selectedPoint.cluster_id!)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                <span>Investigate Cluster</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            )}
            <button
              onClick={() => setSelectedPoint(null)}
              className="px-2.5 py-1.5 rounded text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
