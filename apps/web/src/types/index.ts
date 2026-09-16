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

export interface FactorBreakdownItem {
  name: string;
  weight_pct: number;
  max_points: number;
  raw_value: string;
  normalized_score: number;
  points_earned: number;
  benchmark: string;
  methodology: string;
}

export type FactorBreakdown = Record<string, FactorBreakdownItem>;

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
  factor_breakdown?: FactorBreakdown;
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
  factor_breakdown?: FactorBreakdown;
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
    factor_breakdown?: FactorBreakdown;
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
  factor_breakdown?: FactorBreakdown;
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
    factor_breakdown?: FactorBreakdown;
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

export interface AgentFinding {
  id: string;
  investigation_id: string;
  agent_role: 'investigator' | 'analytics' | 'red_team' | 'regulatory' | 'capa';
  agent_name: string;
  statement: string;
  classification: 'OBSERVED' | 'INFERRED' | 'UNKNOWN';
  confidence: number;
  evidence_claim_ids: string[];
  contradiction_claim_ids: string[];
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface ToolExecutionLog {
  id: string;
  investigation_id: string;
  agent_role: string;
  tool_name: string;
  input_params: Record<string, any>;
  output_summary?: string;
  output_data: Record<string, any>;
  status: 'SUCCESS' | 'UNAVAILABLE' | 'ERROR';
  duration_ms: number;
  evidence_refs: string[];
  created_at: string;
}

export interface DSection {
  title: string;
  content: string;
  status: string;
  evidence: string[];
}

export interface Report8D {
  cluster_id: string;
  cluster_label: string;
  generated_at: string;
  d1_team: DSection;
  d2_problem_description: DSection;
  d3_containment_action: DSection;
  d4_root_cause: DSection;
  d5_corrective_action: DSection;
  d6_validation_plan: DSection;
  d7_prevention_action: DSection;
  d8_closure_and_cost: DSection;
}

export interface TSBDraft {
  tsb_id: string;
  cluster_id: string;
  title: string;
  issue_date: string;
  condition: string;
  affected_vehicles: string;
  symptoms_observed: string[];
  diagnostic_procedure: string;
  interim_repair_recommendation: string;
  parts_information: string;
  warranty_coding_guidance: string;
  evidence_claims: string[];
}

export interface ManifoldPoint {
  claim_id: string;
  external_id: string;
  x: number;
  y: number;
  cluster_id: string | null;
  cluster_index: number;
  cluster_label: string;
  is_noise: boolean;
  is_mismatch: number;
  mismatch_severity: string;
  failure_code: string;
  plant: string;
  model: string;
  date: string | null;
  component: string;
  symptom: string;
  narrative: string;
}

export interface ManifoldCluster {
  cluster_id: string;
  cluster_index: number;
  label: string;
  claim_count: number;
  alert_score: number;
  alert_level: 'CRITICAL' | 'HIGH' | 'WATCH' | 'NORMAL';
  centroid: { x: number; y: number };
  hull: [number, number][];
  primary_component?: string;
  primary_symptom?: string;
}

export interface SemanticManifoldData {
  points: ManifoldPoint[];
  clusters: ManifoldCluster[];
  total_points: number;
  method: string;
  grid_bounds: { min_x: number; max_x: number; min_y: number; max_y: number };
}

export interface LiveStreamStage {
  stage: string;
  agent: string;
  role: 'investigator' | 'analytics' | 'red_team' | 'regulatory' | 'capa';
  description: string;
  status: 'pending' | 'running' | 'completed';
  thoughts: string[];
  tools: Array<{
    tool: string;
    status: string;
    input: Record<string, any>;
    output_summary?: string;
    duration_ms?: number;
  }>;
  findings: Array<{
    statement: string;
    classification: 'OBSERVED' | 'INFERRED' | 'UNKNOWN';
    confidence: number;
    evidence_count: number;
  }>;
  challenges: Array<{
    check: string;
    verdict: string;
    rationale: string;
    confidence_impact: number;
  }>;
}

export interface InvestigationDetail {
  id: string;
  cluster_id: string;
  status: string;
  decision: 'unreviewed' | 'confirmed' | 'rejected' | 'needs_evidence';
  decision_rationale?: string | null;
  reviewer: string;
  summary_conclusion?: string;
  confidence: number;
  overall_classification: string;
  supporting_claims_count: number;
  contradicting_claims_count: number;
  unknowns: string[];
  recommendations: string[];
  metrics_snapshot: Record<string, any>;
  execution_time_ms: number;
  created_at: string;
  updated_at: string;
  findings: AgentFinding[];
  tool_logs: ToolExecutionLog[];
  report_8d?: Report8D;
  tsb_draft?: TSBDraft;
}



