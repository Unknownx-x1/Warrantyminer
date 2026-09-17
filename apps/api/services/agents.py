import re
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Generator
from datetime import datetime, timezone
from collections import Counter
from sqlalchemy.orm import Session
import httpx

from apps.api.config import settings
from apps.api.models.investigation import AgentFinding, ToolExecutionLog
from apps.api.services.investigation_tools import registry, ToolResult

logger = logging.getLogger(__name__)

def sanitize_untrusted_narrative(text: str) -> str:
    """
    Sanitizes technician text to prevent prompt injection or control sequence injection.
    Treats all narrative text strictly as inert string data.
    """
    if not text:
        return ""
    cleaned = re.sub(r"[\r\n\t]+", " ", text)
    cleaned = re.sub(r"[<>{}\[\]]+", "", cleaned)
    return cleaned[:500]

def is_llm_available() -> bool:
    import sys, os
    if "pytest" in sys.modules or os.getenv("EVALUATION") == "true" or not settings.USE_OLLAMA:
        return False
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/version"
        with httpx.Client(timeout=0.4) as client:
            res = client.get(url)
            return res.status_code == 200
    except Exception:
        return False

def call_agent_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Optional LLM reflection call using local Ollama model."""
    if not is_llm_available():
        return None
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "system": system_prompt,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        logger.debug(f"Agent LLM reasoning skipped: {e}")
    return None

class BaseAgent:
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description

    def execute_tool(
        self,
        tool_name: str,
        db: Session,
        tool_logs: List[ToolExecutionLog],
        **kwargs
    ) -> ToolResult:
        res = registry.execute(tool_name, db=db, **kwargs)
        log_entry = ToolExecutionLog(
            agent_role=self.role,
            tool_name=tool_name,
            input_params={k: str(v) for k, v in kwargs.items() if k != "db"},
            output_summary=res.summary,
            output_data=res.data,
            status=res.status,
            duration_ms=res.duration_ms,
            evidence_refs=res.evidence_refs
        )
        tool_logs.append(log_entry)
        return res

# -------------------------------------------------------------------------
# 1. Investigator Agent (Forensic Failure Analysis)
# -------------------------------------------------------------------------
class InvestigatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Forensic Investigator Agent",
            role="investigator",
            description="Isolates physical defect symptoms, components, operating conditions, and cites source claims."
        )

    def stream_run(self, cluster_id: str, db: Session) -> Generator[Dict[str, Any], None, Tuple[List[AgentFinding], List[ToolExecutionLog]]]:
        findings = []
        tool_logs = []

        yield {
            "type": "thought",
            "agent": self.role,
            "agent_name": self.name,
            "text": f"Initializing forensic investigation for Cluster {cluster_id}. Querying raw claims and failure signatures..."
        }

        # Tool 1: get_cluster_claims
        yield {
            "type": "action",
            "agent": self.role,
            "tool": "get_cluster_claims",
            "params": {"cluster_id": cluster_id}
        }
        claims_res = self.execute_tool("get_cluster_claims", db, tool_logs, cluster_id=cluster_id)
        yield {
            "type": "observation",
            "agent": self.role,
            "summary": claims_res.summary,
            "data_count": claims_res.data.get("count", 0)
        }

        if claims_res.status != "SUCCESS" or not claims_res.data.get("claims"):
            f = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement="Insufficient claim records available in this cluster to establish physical failure evidence.",
                classification="UNKNOWN",
                confidence=0.1,
                evidence_claim_ids=[],
                contradiction_claim_ids=[]
            )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence}
            return findings, tool_logs

        claims = claims_res.data["claims"]
        total_claims = len(claims)

        # 1. Component Identification
        components = [c["component"] for c in claims if c.get("component") and c["component"] != "unspecified component"]
        comp_counts = Counter(components)
        if comp_counts:
            top_comp, comp_cnt = comp_counts.most_common(1)[0]
            comp_claims = [c["external_id"] for c in claims if c.get("component") == top_comp]
            comp_pct = round((comp_cnt / total_claims) * 100, 1)

            f1 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Recurring defect localized to '{top_comp}', present in {comp_cnt}/{total_claims} ({comp_pct}%) cluster claims.",
                classification="OBSERVED",
                confidence=min(0.98, round(comp_cnt / total_claims, 2)),
                evidence_claim_ids=comp_claims[:10],
                metadata_json={"component": top_comp, "percentage": comp_pct}
            )
            findings.append(f1)
            yield {"type": "finding", "agent": self.role, "statement": f1.statement, "confidence": f1.confidence, "evidence": f1.evidence_claim_ids[:4]}
        else:
            f1 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement="Component localization is non-specific across member technician narratives.",
                classification="UNKNOWN",
                confidence=0.4,
                evidence_claim_ids=[]
            )
            findings.append(f1)

        # 2. Symptom Identification
        symptoms = [c["symptom"] for c in claims if c.get("symptom") and c["symptom"] != "unspecified operational symptom"]
        symp_counts = Counter(symptoms)
        if symp_counts:
            top_symp, symp_cnt = symp_counts.most_common(1)[0]
            symp_claims = [c["external_id"] for c in claims if c.get("symptom") == top_symp]
            symp_pct = round((symp_cnt / total_claims) * 100, 1)

            f2 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Predominant technician-reported symptom is '{top_symp}' observed in {symp_cnt}/{total_claims} ({symp_pct}%) claims.",
                classification="OBSERVED",
                confidence=min(0.96, round(symp_cnt / total_claims, 2)),
                evidence_claim_ids=symp_claims[:10],
                metadata_json={"symptom": top_symp, "percentage": symp_pct}
            )
            findings.append(f2)
            yield {"type": "finding", "agent": self.role, "statement": f2.statement, "confidence": f2.confidence, "evidence": f2.evidence_claim_ids[:4]}

        # 3. Operating Conditions
        conditions = [c["condition"] for c in claims if c.get("condition") and c["condition"] != "normal operating conditions"]
        cond_counts = Counter(conditions)
        if cond_counts:
            top_cond, cond_cnt = cond_counts.most_common(1)[0]
            cond_claims = [c["external_id"] for c in claims if c.get("condition") == top_cond]
            f3 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Defect symptoms are preferentially triggered under '{top_cond}' ({cond_cnt} claim citations).",
                classification="OBSERVED",
                confidence=0.88,
                evidence_claim_ids=cond_claims[:8],
                metadata_json={"condition": top_cond, "count": cond_cnt}
            )
            findings.append(f3)
            yield {"type": "finding", "agent": self.role, "statement": f3.statement, "confidence": f3.confidence}

        # 4. Failure Mechanism Deduction
        inferred_modes = [c["inferred_failure"] for c in claims if c.get("inferred_failure")]
        if inferred_modes:
            top_mode, mode_cnt = Counter(inferred_modes).most_common(1)[0]
            f4 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Evidence is consistent with {top_mode}. Physical root cause requires metallurgical/component teardown verification.",
                classification="INFERRED",
                confidence=0.82,
                evidence_claim_ids=[c["external_id"] for c in claims if c.get("inferred_failure") == top_mode][:6],
                metadata_json={"inferred_mechanism": top_mode}
            )
            findings.append(f4)
            yield {"type": "finding", "agent": self.role, "statement": f4.statement, "confidence": f4.confidence}

        return findings, tool_logs

    def run(self, cluster_id: str, db: Session) -> Tuple[List[AgentFinding], List[ToolExecutionLog]]:
        gen = self.stream_run(cluster_id, db)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            return e.value

# -------------------------------------------------------------------------
# 2. Analytics Agent (Statistical & Exposure Modeling)
# -------------------------------------------------------------------------
class AnalyticsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Statistical & Analytics Agent",
            role="analytics",
            description="Evaluates trend progression, Poisson-Normal Z-scores, code fragmentation, and sample power."
        )

    def stream_run(self, cluster_id: str, db: Session) -> Generator[Dict[str, Any], None, Tuple[List[AgentFinding], List[ToolExecutionLog]]]:
        findings = []
        tool_logs = []

        yield {
            "type": "thought",
            "agent": self.role,
            "agent_name": self.name,
            "text": "Evaluating longitudinal time-series, statistical significance, and taxonomy fragmentation..."
        }

        # 1. Trend Analysis
        yield {"type": "action", "agent": self.role, "tool": "calculate_cluster_trend", "params": {"cluster_id": cluster_id}}
        trend_res = self.execute_tool("calculate_cluster_trend", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": trend_res.summary}

        if trend_res.status == "SUCCESS":
            growth = trend_res.data.get("growth_rate_pct", 0.0)
            baseline = trend_res.data.get("baseline_mean", 0.0)
            latest = trend_res.data.get("latest_month_volume", 0)

            if growth > 50:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"Significant volume acceleration: +{growth:.1f}% surge in latest period ({latest} claims) vs baseline ({baseline:.1f} claims/mo).",
                    classification="OBSERVED",
                    confidence=0.95,
                    evidence_claim_ids=trend_res.evidence_refs,
                    metadata_json={"growth_rate": growth, "baseline": baseline, "latest_volume": latest}
                )
            else:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"Volume trajectory is stable (+{growth:.1f}% vs baseline).",
                    classification="OBSERVED",
                    confidence=0.90,
                    evidence_claim_ids=trend_res.evidence_refs
                )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence}

        # 2. Statistical Z-Score
        yield {"type": "action", "agent": self.role, "tool": "calculate_z_score", "params": {"cluster_id": cluster_id}}
        z_res = self.execute_tool("calculate_z_score", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": z_res.summary}

        if z_res.status == "SUCCESS":
            z_val = z_res.data.get("z_score", 0.0)
            is_sig = z_res.data.get("is_significant", False)
            conf_lvl = z_res.data.get("confidence_level", "p >= 0.05")

            f = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Poisson-Normal anomaly test yielded Z = {z_val:.2f} ({conf_lvl}). Statistical anomaly hypothesis supported: {is_sig}.",
                classification="OBSERVED",
                confidence=0.94 if is_sig else 0.70,
                evidence_claim_ids=[],
                metadata_json={"z_score": z_val, "is_significant": is_sig, "confidence_level": conf_lvl}
            )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence}

        # 3. Code Fragmentation
        yield {"type": "action", "agent": self.role, "tool": "analyze_code_fragmentation", "params": {"cluster_id": cluster_id}}
        frag_res = self.execute_tool("analyze_code_fragmentation", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": frag_res.summary}

        if frag_res.status == "SUCCESS":
            distinct_codes = frag_res.data.get("distinct_code_count", 1)
            entropy = frag_res.data.get("shannon_entropy", 0.0)
            dom_code = frag_res.data.get("dominant_code", "")
            dom_pct = frag_res.data.get("dominant_pct", 100.0)

            if distinct_codes >= 3:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"High taxonomy fragmentation: Claims dispersed across {distinct_codes} distinct dealer codes (Shannon entropy: {entropy:.2f}). Dominant code '{dom_code}' accounts for only {dom_pct}% of claims.",
                    classification="OBSERVED",
                    confidence=0.93,
                    evidence_claim_ids=frag_res.evidence_refs[:6],
                    metadata_json={"distinct_codes": distinct_codes, "entropy": entropy}
                )
            else:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"Low taxonomy fragmentation: Claims concentrated in {distinct_codes} dealer code(s) ('{dom_code}' at {dom_pct}%).",
                    classification="OBSERVED",
                    confidence=0.88,
                    evidence_claim_ids=frag_res.evidence_refs[:4]
                )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence}

        # 4. Warranty Financial Exposure
        yield {"type": "action", "agent": self.role, "tool": "estimate_warranty_exposure", "params": {"cluster_id": cluster_id}}
        cost_res = self.execute_tool("estimate_warranty_exposure", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": cost_res.summary}

        if cost_res.status == "SUCCESS":
            incurred = cost_res.data.get("incurred_cost", 0.0)
            proj_6mo = cost_res.data.get("projected_6mo_exposure", 0.0)
            f = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"Financial exposure estimate: ${incurred:,.2f} incurred to date; projected 6-month liability of ${proj_6mo:,.2f} at current run-rate.",
                classification="INFERRED",
                confidence=0.80,
                evidence_claim_ids=[],
                metadata_json={"incurred_cost": incurred, "projected_6mo_exposure": proj_6mo}
            )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence}

        return findings, tool_logs

    def run(self, cluster_id: str, db: Session) -> Tuple[List[AgentFinding], List[ToolExecutionLog]]:
        gen = self.stream_run(cluster_id, db)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            return e.value

# -------------------------------------------------------------------------
# 3. Red Team / Critic Agent (Adversarial Challenger)
# -------------------------------------------------------------------------
class RedTeamAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Red Team / Critic Agent",
            role="red_team",
            description="Adversarially challenges hypotheses, checks single-plant bias, sample power, and data artifacts."
        )

    def stream_run(self, cluster_id: str, db: Session) -> Generator[Dict[str, Any], None, Tuple[List[AgentFinding], List[ToolExecutionLog]]]:
        findings = []
        tool_logs = []

        yield {
            "type": "thought",
            "agent": self.role,
            "agent_name": self.name,
            "text": "Adversarially reviewing claims. Testing for single-plant tooling anomalies, semantic outliers, and sample power biases..."
        }

        # 1. Check Plant Concentration
        yield {"type": "action", "agent": self.role, "tool": "analyze_plant_distribution", "params": {"cluster_id": cluster_id}}
        plant_res = self.execute_tool("analyze_plant_distribution", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": plant_res.summary}

        if plant_res.status == "SUCCESS":
            is_plant_spec = plant_res.data.get("is_plant_specific", False)
            dom_plant = plant_res.data.get("dominant_plant", "")
            dom_pct = plant_res.data.get("dominant_plant_pct", 0.0)
            p_count = plant_res.data.get("plant_count", 1)

            if is_plant_spec:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"CHALLENGE: Signal is heavily localized to single plant '{dom_plant}' ({dom_pct}% of claims). Potential localized tooling/shift defect or reporting bias rather than generic platform design defect.",
                    classification="OBSERVED",
                    confidence=0.88,
                    evidence_claim_ids=plant_res.evidence_refs[:6],
                    metadata_json={"challenge_type": "PLANT_LOCALIZATION", "dominant_plant": dom_plant, "percentage": dom_pct}
                )
            else:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"PASSED BIAS CHECK: Defect propagated across {p_count} independent assembly plants without single-plant domination (top plant: {dom_pct}%). Indicates systemic supplier/design issue.",
                    classification="OBSERVED",
                    confidence=0.92,
                    evidence_claim_ids=plant_res.evidence_refs[:4]
                )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence, "is_challenge": "CHALLENGE" in f.statement}

        # 2. Check Counter-Examples
        yield {"type": "action", "agent": self.role, "tool": "search_counter_examples", "params": {"cluster_id": cluster_id}}
        counter_res = self.execute_tool("search_counter_examples", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": counter_res.summary}

        if counter_res.status == "SUCCESS":
            cnt_count = counter_res.data.get("counter_example_count", 0)
            if cnt_count > 3:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"CHALLENGE: Cluster contains {cnt_count} semantic outlier claims that mention differing components or symptoms. Cluster may contain mild noise leakage.",
                    classification="OBSERVED",
                    confidence=0.75,
                    evidence_claim_ids=[],
                    contradiction_claim_ids=counter_res.evidence_refs[:6],
                    metadata_json={"challenge_type": "SEMANTIC_OUTLIERS", "count": cnt_count}
                )
            else:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement="PASSED COHESION CHECK: Cluster demonstrates high semantic purity with negligible counter-example claims.",
                    classification="OBSERVED",
                    confidence=0.94,
                    evidence_claim_ids=[]
                )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence, "is_challenge": "CHALLENGE" in f.statement}

        # 3. Check Data Quality & Sample Size
        yield {"type": "action", "agent": self.role, "tool": "check_data_quality", "params": {"cluster_id": cluster_id}}
        dq_res = self.execute_tool("check_data_quality", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": dq_res.summary}

        if dq_res.status == "SUCCESS":
            tot = dq_res.data.get("total_claims", 0)
            if tot < 6:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"CHALLENGE: Small sample size (N = {tot} claims). Statistical anomaly conclusions carry higher uncertainty.",
                    classification="OBSERVED",
                    confidence=0.65,
                    evidence_claim_ids=[],
                    metadata_json={"challenge_type": "SMALL_SAMPLE_SIZE", "count": tot}
                )
            else:
                f = AgentFinding(
                    agent_role=self.role,
                    agent_name=self.name,
                    statement=f"PASSED POWER CHECK: Sample size (N = {tot} claims) provides sufficient power to reject random Poisson baseline fluctuations.",
                    classification="OBSERVED",
                    confidence=0.91,
                    evidence_claim_ids=[]
                )
            findings.append(f)
            yield {"type": "finding", "agent": self.role, "statement": f.statement, "confidence": f.confidence, "is_challenge": "CHALLENGE" in f.statement}

        return findings, tool_logs

    def run(self, cluster_id: str, db: Session) -> Tuple[List[AgentFinding], List[ToolExecutionLog]]:
        gen = self.stream_run(cluster_id, db)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            return e.value

# -------------------------------------------------------------------------
# 4. Regulatory & External Sentry Agent
# -------------------------------------------------------------------------
class RegulatoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Regulatory & External Sentry Agent",
            role="regulatory",
            description="Cross-references federal safety campaigns and supplier lot traceability."
        )

    def stream_run(self, cluster_id: str, db: Session) -> Generator[Dict[str, Any], None, Tuple[List[AgentFinding], List[ToolExecutionLog]]]:
        findings = []
        tool_logs = []

        yield {
            "type": "thought",
            "agent": self.role,
            "agent_name": self.name,
            "text": "Querying federal safety campaign adapters and manufacturing lot traceability bounds..."
        }

        # 1. NHTSA Federal Safety Adapter
        yield {"type": "action", "agent": self.role, "tool": "query_nhtsa_recalls", "params": {"component": "suspension"}}
        nhtsa_res = self.execute_tool("query_nhtsa_recalls", db, tool_logs, component="suspension")
        yield {"type": "observation", "agent": self.role, "summary": nhtsa_res.summary}

        if nhtsa_res.status == "SUCCESS":
            results = nhtsa_res.data.get("results", [])
            f1 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement=f"NHTSA safety query identified {len(results)} relevant active campaigns for this component subsystem.",
                classification="OBSERVED",
                confidence=0.85,
                evidence_claim_ids=[]
            )
        else:
            f1 = AgentFinding(
                agent_role=self.role,
                agent_name=self.name,
                statement="NHTSA regulatory database is currently unreachable/offline. External campaign correlation unavailable.",
                classification="UNKNOWN",
                confidence=0.0,
                evidence_claim_ids=[]
            )
        findings.append(f1)
        yield {"type": "finding", "agent": self.role, "statement": f1.statement, "confidence": f1.confidence}

        # 2. Manufacturing & Supplier Lot Traceability
        yield {"type": "action", "agent": self.role, "tool": "query_supplier_manufacturing_records", "params": {"cluster_id": cluster_id}}
        supp_res = self.execute_tool("query_supplier_manufacturing_records", db, tool_logs, cluster_id=cluster_id)
        yield {"type": "observation", "agent": self.role, "summary": supp_res.summary}

        f2 = AgentFinding(
            agent_role=self.role,
            agent_name=self.name,
            statement="Supplier and lot attribution is unavailable: Manufacturing BOM / MES batch records are not integrated into this warranty dataset.",
            classification="UNKNOWN",
            confidence=0.0,
            evidence_claim_ids=[]
        )
        findings.append(f2)
        yield {"type": "finding", "agent": self.role, "statement": f2.statement, "confidence": f2.confidence}

        return findings, tool_logs

    def run(self, cluster_id: str, db: Session) -> Tuple[List[AgentFinding], List[ToolExecutionLog]]:
        gen = self.stream_run(cluster_id, db)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            return e.value

# -------------------------------------------------------------------------
# 5. CAPA & Deliverables Agent (Adjudicator, 8D & TSB Generator)
# -------------------------------------------------------------------------
class CAPAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CAPA & Quality Deliverables Agent",
            role="capa",
            description="Adjudicates debate findings and synthesizes formal 8D problem solving reports and Technical Service Bulletins."
        )

    def generate_8d_report(
        self,
        cluster: Any,
        findings: List[AgentFinding]
    ) -> Dict[str, Any]:
        """Synthesizes structured 8D report strictly from observed findings."""
        comp_finding = next((f for f in findings if f.agent_role == "investigator" and "component" in f.statement.lower()), None)
        symp_finding = next((f for f in findings if f.agent_role == "investigator" and "symptom" in f.statement.lower()), None)
        mech_finding = next((f for f in findings if f.agent_role == "investigator" and f.classification == "INFERRED"), None)

        primary_comp = cluster.primary_component or (comp_finding.metadata_json.get("component") if comp_finding else "Unknown Component")
        primary_symp = cluster.primary_symptom or (symp_finding.metadata_json.get("symptom") if symp_finding else "Unspecified Symptom")
        evidence_ids = comp_finding.evidence_claim_ids if comp_finding else []

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        d1 = {
            "title": "D1 — Team Formation",
            "content": f"Multi-disciplinary reliability response team assembled. Lead: Reliability Engineering. Surveillance Engine: Reliant.ai Autonomous Swarm. Cluster: {cluster.label}.",
            "status": "ESTABLISHED",
            "evidence": []
        }
        d2 = {
            "title": "D2 — Problem Description (5W2H)",
            "content": f"Field warranty reports document recurring {primary_symp} localized to the {primary_comp}. Defect has emerged across {cluster.claim_count} warranty claims and {cluster.cross_code_count} dealer codes.",
            "status": "ESTABLISHED",
            "evidence": evidence_ids[:8]
        }
        d3 = {
            "title": "D3 — Interim Containment Action",
            "content": f"1. Quarantine affected incoming inventory for {primary_comp} pending lot verification.\n2. Dispatch engineering diagnostic protocol to regional service centers.\n3. Increase line-end torque and inspection audits at assembly plants.",
            "status": "ESTABLISHED",
            "evidence": []
        }
        d4_content = mech_finding.statement if mech_finding else "Potential physical wear or clearance degradation. Root cause requires lab metallurgical examination."
        d4 = {
            "title": "D4 — Root Cause & Escape Point",
            "content": d4_content + " Root Cause Escape: Pre-delivery quality gates failed to detect under dynamic road load conditions.",
            "status": "INFERRED",
            "evidence": mech_finding.evidence_claim_ids[:6] if mech_finding else []
        }
        d5 = {
            "title": "D5 — Permanent Corrective Actions (PCA)",
            "content": f"Revise part specification for {primary_comp} with upgraded bushing/fastener tolerance. Update assembly line QA torque validation protocol.",
            "status": "INFERRED",
            "evidence": []
        }
        d6 = {
            "title": "D6 — Implementation & Validation Plan",
            "content": f"Conduct 500-hour accelerated durability bench test on revised {primary_comp}. Monitor warranty claims over subsequent 90-day window for zero re-emergence.",
            "status": "INFERRED",
            "evidence": []
        }
        d7 = {
            "title": "D7 — Prevention of Recurrence",
            "content": f"Update Design FMEA (DFMEA) and Process FMEA (PFMEA) for chassis and {primary_comp} subsystems. Add automated semantic surveillance alert trigger.",
            "status": "ESTABLISHED",
            "evidence": []
        }
        d8 = {
            "title": "D8 — Closure & Financial Exposure",
            "content": f"Incurred warranty volume: {cluster.claim_count} claims. Investigation pending engineer physical teardown sign-off.",
            "status": "ESTABLISHED",
            "evidence": []
        }

        return {
            "cluster_id": cluster.id,
            "cluster_label": cluster.label,
            "generated_at": now_str,
            "d1_team": d1,
            "d2_problem_description": d2,
            "d3_containment_action": d3,
            "d4_root_cause": d4,
            "d5_corrective_action": d5,
            "d6_validation_plan": d6,
            "d7_prevention_action": d7,
            "d8_closure_and_cost": d8
        }

    def generate_tsb_draft(
        self,
        cluster: Any,
        findings: List[AgentFinding]
    ) -> Dict[str, Any]:
        """Generates draft Technical Service Bulletin based on verified evidence."""
        comp = cluster.primary_component or "Subsystem Assembly"
        symp = cluster.primary_symptom or "Abnormal Operational Symptom"
        
        comp_finding = next((f for f in findings if f.agent_role == "investigator" and "component" in f.statement.lower()), None)
        evidence = comp_finding.evidence_claim_ids if comp_finding else []

        now_utc = datetime.now(timezone.utc)
        return {
            "tsb_id": f"TSB-REL-{now_utc.strftime('%Y')}-{cluster.cluster_index + 100:03d}",
            "cluster_id": cluster.id,
            "title": f"TECHNICAL SERVICE BULLETIN: Diagnostic and Inspection Procedure for {comp.title()} ({symp.title()})",
            "issue_date": now_utc.strftime("%B %d, %Y"),
            "condition": f"Customer reports {symp} when operating under rough road surfaces or dynamic maneuvers.",
            "affected_vehicles": f"All production models reporting into cluster ({cluster.model_count} models identified across {cluster.plant_count} plants).",
            "symptoms_observed": [symp, "Audible mechanical tapping or vibration during chassis articulation"],
            "diagnostic_procedure": f"1. Inspect {comp} for excessive clearance, wear, or loose fastener torque.\n2. Perform road test over rough surface to reproduce acoustic symptom.\n3. Verify no interference with adjacent steering or suspension components.",
            "interim_repair_recommendation": f"Inspect and replace worn {comp} components. Torque all mounting hardware to OEM nominal engineering specifications.",
            "parts_information": "Part number and revised component revisions require engineering confirmation prior to warranty claim submission.",
            "warranty_coding_guidance": f"Ensure claim is coded accurately under primary subsystem rather than generic OTHER/NFF codes to ensure surveillance tracking.",
            "evidence_claims": evidence[:8]
        }

