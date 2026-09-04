import {
  Claim,
  ClaimsListResponse,
  ClusterListItem,
  ClusterDetail,
  ClusterClaimItem,
  DashboardSummary,
  BaselineComparison,
  DefectFingerprint,
  MatchResult,
  AnalysisRunResponse
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    }
  });
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errObj = await res.json();
      if (errObj.detail) errorMsg = errObj.detail;
    } catch {}
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // Summary & Alerts
  getSummary: () => fetchJson<DashboardSummary>(`${API_BASE}/alerts/summary`),
  getAlerts: () => fetchJson<ClusterListItem[]>(`${API_BASE}/alerts`),

  // Clusters
  getClusters: (alertLevel?: string, sortBy?: string) => {
    const params = new URLSearchParams();
    if (alertLevel) params.append('alert_level', alertLevel);
    if (sortBy) params.append('sort_by', sortBy);
    return fetchJson<ClusterListItem[]>(`${API_BASE}/clusters?${params.toString()}`);
  },
  getClusterDetail: (clusterId: string) => fetchJson<ClusterDetail>(`${API_BASE}/clusters/${clusterId}`),
  getClusterClaims: (clusterId: string) => 
    fetchJson<{ cluster_id: string; cluster_label: string; total: number; claims: ClusterClaimItem[] }>(
      `${API_BASE}/clusters/${clusterId}/claims`
    ),

  // Claims Explorer
  getClaims: (params: {
    search?: string;
    failure_code?: string;
    product_model?: string;
    plant?: string;
    mismatch_only?: boolean;
    cluster_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.failure_code) query.append('failure_code', params.failure_code);
    if (params.product_model) query.append('product_model', params.product_model);
    if (params.plant) query.append('plant', params.plant);
    if (params.mismatch_only) query.append('mismatch_only', 'true');
    if (params.cluster_id) query.append('cluster_id', params.cluster_id);
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());
    return fetchJson<ClaimsListResponse>(`${API_BASE}/claims?${query.toString()}`);
  },
  getClaimDetail: (claimId: string) => fetchJson<Claim>(`${API_BASE}/claims/${claimId}`),

  // Baseline Comparison
  getBaselineComparison: (clusterId?: string) => {
    const params = clusterId ? `?cluster_id=${clusterId}` : '';
    return fetchJson<BaselineComparison>(`${API_BASE}/baseline/comparison${params}`);
  },

  // Pipeline Analysis
  runAnalysis: (options?: { min_cluster_size?: number; force_recompute?: boolean }) =>
    fetchJson<AnalysisRunResponse>(`${API_BASE}/analysis/run`, {
      method: 'POST',
      body: JSON.stringify({
        min_cluster_size: options?.min_cluster_size,
        force_recompute: options?.force_recompute ?? true
      })
    }),

  // File Upload
  uploadClaims: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/claims/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload file');
    return res.json();
  },

  // Feedback & Human Gate
  submitFeedback: (clusterId: string, payload: { decision: 'confirmed' | 'edited' | 'dismissed'; rationale?: string; custom_label?: string; reviewer?: string }) =>
    fetchJson(`${API_BASE}/clusters/${clusterId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),

  // Defect Fingerprints
  getFingerprints: () => fetchJson<DefectFingerprint[]>(`${API_BASE}/fingerprints`),
  matchFingerprint: (payload: { narrative: string; component?: string; symptom?: string }) =>
    fetchJson<MatchResult[]>(`${API_BASE}/fingerprints/match`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),

  // Database Reset
  resetDatabase: () =>
    fetchJson<{ status: string; message: string; deleted: Record<string, number> }>(`${API_BASE}/claims/reset`, {
      method: 'POST'
    })
};
