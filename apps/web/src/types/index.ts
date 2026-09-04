export interface FailureSignature {
  component?: string | null;
  symptom?: string | null;
  condition?: string | null;
  severity?: string | null;
  inferred_failure?: string | null;
  contributing_factors?: string[];
  extraction_confidence: number;
}

export interface CodeMismatch {
  assigned_code?: string | null;
  inferred_category?: string | null;
  mismatch_severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'NORMAL';
  is_mismatch: number;
  mismatch_score: number;
  reason?: string | null;
  confidence: number;
}

export interface Claim {
  id: string;
  external_claim_id: string;
  claim_date: string;
  product_model?: string | null;
  plant?: string | null;
  failure_code?: string | null;
  narrative: string;
  source?: string | null;
  created_at: string;
  signature?: FailureSignature | null;
  mismatch?: CodeMismatch | null;
  cluster_id?: string | null;
  cluster_label?: string | null;
}

export interface ClaimsListResponse {
  total: number;
  items: Claim[];
  page: number;
  page_size: number;
}

export interface TimePoint {
  period: string;
  claim_count: number;
  baseline: number;
  z_score?: number;
}

export interface AIRationale {
  why_grouped: string;
  why_alerted: string;
  key_symptoms: string[];
  affected_components: string[];
}

export interface ClusterListItem {
  id: string;
  run_id?: string;
  cluster_index: number;
  label: string;
  description?: string;
  primary_component?: string;
  primary_symptom?: string;
  claim_count: number;
  cross_code_count: number;
  plant_count: number;
  model_count: number;
  growth_rate: number;
  significance_score: number;
  coherence_score: number;
  alert_score: number;
  alert_level: 'CRITICAL' | 'HIGH' | 'WATCH' | 'NORMAL';
  status: 'unreviewed' | 'confirmed' | 'edited' | 'dismissed';
  created_at: string;
  top_codes: Record<string, number>;
}

export interface ClusterDetail extends ClusterListItem {
  baseline_volume: number;
  current_volume: number;
  cusum_score: number;
  code_distribution: Record<string, number>;
  plant_distribution: Record<string, number>;
  model_distribution: Record<string, number>;
  time_series: TimePoint[];
  representative_claims: Array<{
    claim_id: string;
    failure_code?: string;
    plant?: string;
    narrative: string;
  }>;
  ai_rationale?: AIRationale;
  feedback?: {
    decision: string;
    rationale?: string;
    reviewer: string;
    custom_label?: string;
    created_at?: string;
  };
}

export interface ClusterClaimItem {
  claim_id: string;
  external_claim_id: string;
  claim_date: string;
  product_model?: string;
  plant?: string;
  failure_code?: string;
  narrative: string;
  component?: string;
  symptom?: string;
  inferred_failure?: string;
  is_mismatch: number;
  mismatch_severity: string;
  mismatch_reason?: string;
  similarity_score: number;
}

export interface DashboardSummary {
  claims_analyzed: number;
  emerging_patterns: number;
  high_risk_patterns: number;
  critical_patterns: number;
  high_patterns: number;
  watch_patterns: number;
  miscoded_claims: number;
  hero_cluster?: {
    id: string;
    label: string;
    alert_level: string;
    alert_score: number;
    growth_rate: number;
    claim_count: number;
    cross_code_count: number;
    plant_count: number;
    description?: string;
    primary_component?: string;
    primary_symptom?: string;
    significance_score?: number;
    cusum_score?: number;
    baseline_volume?: number;
    current_volume?: number;
    code_distribution?: Record<string, number>;
    why_alerted?: string;
    time_series?: TimePoint[];
    representative_claims: Array<{
      claim_id: string;
      failure_code?: string;
      plant?: string;
      narrative: string;
    }>;
  };
}

export interface BaselineComparison {
  has_data: boolean;
  cluster_id?: string;
  cluster_label?: string;
  alert_level?: string;
  alert_score?: number;
  growth_rate?: number;
  total_cluster_claims?: number;
  cross_code_count?: number;
  lead_time_days?: number | null;
  lead_time_status?: string;
  semantic_detection_date?: string | null;
  traditional_detection_date?: string | null;
  traditional_monitoring?: {
    title: string;
    status: string;
    detection_date?: string | null;
    explanation: string;
    code_buckets: Array<{
      code: string;
      claim_count: number;
      status: string;
      alert: boolean;
      threshold_reached: boolean;
    }>;
  };
  semantic_monitoring?: {
    title: string;
    status: string;
    detection_date?: string | null;
    explanation: string;
    growth_percentage: number;
    significance_z: number;
    alert_score: number;
  };
}

export interface DefectFingerprint {
  id: string;
  name: string;
  description?: string;
  component?: string;
  symptoms: string[];
  conditions: string[];
  example_claims: string[];
  confirmed_count: string;
  created_at: string;
  updated_at: string;
}

export interface MatchResult {
  fingerprint_id: string;
  fingerprint_name: string;
  component?: string;
  similarity_score: number;
  matched_symptoms: string[];
  confidence: number;
  recommendation: string;
}

export interface AnalysisRunResponse {
  run_id: string;
  status: string;
  total_claims: number;
  clusters_found: number;
  alerts_critical: number;
  alerts_high: number;
  mismatches_detected: number;
  processing_time_ms: number;
  summary: Record<string, any>;
  events?: string[];
  steps?: Record<string, any>;
}

