import time
import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime
from sqlalchemy.orm import Session

from apps.api.models.cluster import Cluster
from apps.api.models.investigation import Investigation, AgentFinding, ToolExecutionLog
from apps.api.services.agents import (
    InvestigatorAgent,
    AnalyticsAgent,
    RedTeamAgent,
    RegulatoryAgent,
    CAPAAgent
)

logger = logging.getLogger(__name__)

class InvestigationOrchestrator:
    def __init__(self):
        self.investigator = InvestigatorAgent()
        self.analytics = AnalyticsAgent()
        self.red_team = RedTeamAgent()
        self.regulatory = RegulatoryAgent()
        self.capa = CAPAAgent()

    def run_investigation(
        self,
        db: Session,
        cluster_id: str,
        force_recompute: bool = False
    ) -> Investigation:
        """
        Executes an autonomous evidence-driven multi-agent engineering investigation for a cluster.
        """
        start_t = time.time()
        cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
        if not cluster:
            raise ValueError(f"Cluster '{cluster_id}' does not exist in database.")

        # Check if recent investigation exists
        if not force_recompute:
            existing = db.query(Investigation).filter(Investigation.cluster_id == cluster_id).order_by(Investigation.created_at.desc()).first()
            if existing and existing.status == "completed":
                return existing

        logger.info(f"Starting autonomous multi-agent investigation for Cluster {cluster_id} ('{cluster.label}')")

        all_findings: List[AgentFinding] = []
        all_tool_logs: List[ToolExecutionLog] = []

        # 1. Execute Core Agents
        inv_findings, inv_tools = self.investigator.run(cluster_id, db)
        all_findings.extend(inv_findings)
        all_tool_logs.extend(inv_tools)

        ana_findings, ana_tools = self.analytics.run(cluster_id, db)
        all_findings.extend(ana_findings)
        all_tool_logs.extend(ana_tools)

        red_findings, red_tools = self.red_team.run(cluster_id, db)
        all_findings.extend(red_findings)
        all_tool_logs.extend(red_tools)

        reg_findings, reg_tools = self.regulatory.run(cluster_id, db)
        all_findings.extend(reg_findings)
        all_tool_logs.extend(reg_tools)

        # 2. Synthesis & Confidence Calculation
        supporting_claim_ids = set()
        contradicting_claim_ids = set()

        for f in all_findings:
            if f.evidence_claim_ids:
                supporting_claim_ids.update(f.evidence_claim_ids)
            if f.contradiction_claim_ids:
                contradicting_claim_ids.update(f.contradiction_claim_ids)

        challenges = [f for f in red_findings if "CHALLENGE" in f.statement]
        
        # Calculate overall confidence
        base_confidence = 0.85
        if challenges:
            base_confidence -= 0.10 * len(challenges)
        if cluster.claim_count >= 15:
            base_confidence += 0.05
        if cluster.growth_rate > 100:
            base_confidence += 0.05
        
        overall_confidence = max(0.20, min(0.98, round(base_confidence, 2)))

        # Determine overall classification
        if len(challenges) >= 2 and cluster.claim_count < 6:
            overall_classification = "INSUFFICIENT_EVIDENCE"
        elif any("PLANT_LOCALIZATION" in str(c.metadata_json) for c in challenges):
            overall_classification = "PLANT_SPECIFIC_ISSUE"
        elif cluster.alert_score >= 60.0:
            overall_classification = "EMERGING_DEFECT"
        else:
            overall_classification = "WATCH_SIGNAL"

        # Generate Unknowns list
        unknowns = [
            "Specific metallurgical failure mode (requires destructive lab teardown)",
            "Supplier lot number attribution (manufacturing MES dataset not connected)",
            "Exact component revision / batch manufacturing date"
        ]

        # Generate Actionable Recommendations
        recommendations = [
            f"Issue containment directive to service centers for {cluster.primary_component or 'affected component'}.",
            f"Request physical return of 5 replaced parts from highest-volume plant for lab examination.",
            f"Cross-reference production line shift logs for affected VINs with supplier quality team."
        ]

        # Executive Summary Conclusion
        comp_name = cluster.primary_component or "unspecified subsystem"
        symp_name = cluster.primary_symptom or "symptoms"
        summary_conclusion = (
            f"Autonomous investigation completed for Cluster '{cluster.label}'. "
            f"Evidence unifies {cluster.claim_count} claims across {cluster.cross_code_count} dealer codes "
            f"describing recurring {symp_name} on {comp_name}. "
            f"Statistical significance (Z = {cluster.significance_score:.2f}) and volume growth (+{cluster.growth_rate:.0f}%) "
            f"indicate an emerging defect with {overall_confidence * 100:.0f}% confidence. "
            f"Red Team completed {len(red_findings)} challenge checks ({len(challenges)} flags raised)."
        )

        # 3. Generate 8D Report and TSB Draft
        report_8d = self.capa.generate_8d_report(cluster, all_findings)
        tsb_draft = self.capa.generate_tsb_draft(cluster, all_findings)

        execution_time_ms = round((time.time() - start_t) * 1000, 2)

        # 4. Create and Persist Investigation Record
        # Delete prior incomplete or unconfirmed investigations for clean state
        prior_invs = db.query(Investigation).filter(Investigation.cluster_id == cluster_id).all()
        for p in prior_invs:
            if p.decision == "unreviewed":
                db.delete(p)
        db.commit()

        investigation = Investigation(
            cluster_id=cluster_id,
            status="completed",
            decision="unreviewed",
            reviewer="Reliability Engineer",
            summary_conclusion=summary_conclusion,
            confidence=overall_confidence,
            overall_classification=overall_classification,
            supporting_claims_count=len(supporting_claim_ids),
            contradicting_claims_count=len(contradicting_claim_ids),
            unknowns=unknowns,
            recommendations=recommendations,
            report_8d=report_8d,
            tsb_draft=tsb_draft,
            metrics_snapshot={
                "claim_count": cluster.claim_count,
                "alert_score": cluster.alert_score,
                "alert_level": cluster.alert_level,
                "growth_rate": cluster.growth_rate,
                "significance_score": cluster.significance_score,
                "cross_code_count": cluster.cross_code_count,
                "plant_count": cluster.plant_count
            },
            execution_time_ms=execution_time_ms
        )
        db.add(investigation)
        db.flush()

        # Link and save findings
        for f in all_findings:
            f.investigation_id = investigation.id
            db.add(f)

        # Link and save tool logs
        for t in all_tool_logs:
            t.investigation_id = investigation.id
            db.add(t)

        db.commit()
        db.refresh(investigation)

        logger.info(f"Investigation {investigation.id} persisted with {len(all_findings)} findings and {len(all_tool_logs)} tool logs in {execution_time_ms}ms")
        return investigation

    def stream_investigation(
        self,
        db: Session,
        cluster_id: str
    ) -> Generator[Dict[str, Any], None, Investigation]:
        """
        Executes multi-agent investigation while streaming real-time thoughts, tool calls, and debate findings.
        """
        start_t = time.time()
        cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
        if not cluster:
            raise ValueError(f"Cluster '{cluster_id}' does not exist.")

        yield {
            "event": "start",
            "cluster_id": cluster_id,
            "cluster_label": cluster.label,
            "claim_count": cluster.claim_count,
            "alert_score": cluster.alert_score,
            "alert_level": cluster.alert_level
        }

        all_findings: List[AgentFinding] = []
        all_tool_logs: List[ToolExecutionLog] = []

        # 1. Investigator Agent Stream
        inv_gen = self.investigator.stream_run(cluster_id, db)
        try:
            while True:
                evt = next(inv_gen)
                yield {"event": "agent_event", **evt}
        except StopIteration as e:
            inv_findings, inv_tools = e.value
            all_findings.extend(inv_findings)
            all_tool_logs.extend(inv_tools)

        # 2. Analytics Agent Stream
        ana_gen = self.analytics.stream_run(cluster_id, db)
        try:
            while True:
                evt = next(ana_gen)
                yield {"event": "agent_event", **evt}
        except StopIteration as e:
            ana_findings, ana_tools = e.value
            all_findings.extend(ana_findings)
            all_tool_logs.extend(ana_tools)

        # 3. Red Team Critic Stream
        red_gen = self.red_team.stream_run(cluster_id, db)
        try:
            while True:
                evt = next(red_gen)
                yield {"event": "agent_event", **evt}
        except StopIteration as e:
            red_findings, red_tools = e.value
            all_findings.extend(red_findings)
            all_tool_logs.extend(red_tools)

        # 4. Regulatory Agent Stream
        reg_gen = self.regulatory.stream_run(cluster_id, db)
        try:
            while True:
                evt = next(reg_gen)
                yield {"event": "agent_event", **evt}
        except StopIteration as e:
            reg_findings, reg_tools = e.value
            all_findings.extend(reg_findings)
            all_tool_logs.extend(reg_tools)

        # 5. Adjudication & Confidence Synthesis
        supporting_claim_ids = set()
        contradicting_claim_ids = set()
        for f in all_findings:
            if f.evidence_claim_ids:
                supporting_claim_ids.update(f.evidence_claim_ids)
            if f.contradiction_claim_ids:
                contradicting_claim_ids.update(f.contradiction_claim_ids)

        challenges = [f for f in red_findings if "CHALLENGE" in f.statement]
        base_confidence = 0.85
        if challenges:
            base_confidence -= 0.10 * len(challenges)
        if cluster.claim_count >= 15:
            base_confidence += 0.05
        if cluster.growth_rate > 100:
            base_confidence += 0.05
        overall_confidence = max(0.20, min(0.98, round(base_confidence, 2)))

        if len(challenges) >= 2 and cluster.claim_count < 6:
            overall_classification = "INSUFFICIENT_EVIDENCE"
        elif any("PLANT_LOCALIZATION" in str(c.metadata_json) for c in challenges):
            overall_classification = "PLANT_SPECIFIC_ISSUE"
        elif cluster.alert_score >= 60.0:
            overall_classification = "EMERGING_DEFECT"
        else:
            overall_classification = "WATCH_SIGNAL"

        unknowns = [
            "Specific metallurgical failure mode (requires destructive lab teardown)",
            "Supplier lot number attribution (manufacturing MES dataset not connected)",
            "Exact component revision / batch manufacturing date"
        ]
        recommendations = [
            f"Issue containment directive to service centers for {cluster.primary_component or 'affected component'}.",
            f"Request physical return of 5 replaced parts from highest-volume plant for lab examination.",
            f"Cross-reference production line shift logs for affected VINs with supplier quality team."
        ]
        comp_name = cluster.primary_component or "unspecified subsystem"
        symp_name = cluster.primary_symptom or "symptoms"
        summary_conclusion = (
            f"Autonomous investigation completed for Cluster '{cluster.label}'. "
            f"Evidence unifies {cluster.claim_count} claims across {cluster.cross_code_count} dealer codes "
            f"describing recurring {symp_name} on {comp_name}. "
            f"Statistical significance (Z = {cluster.significance_score:.2f}) and volume growth (+{cluster.growth_rate:.0f}%) "
            f"indicate an emerging defect with {overall_confidence * 100:.0f}% confidence. "
            f"Red Team completed {len(red_findings)} challenge checks ({len(challenges)} flags raised)."
        )

        report_8d = self.capa.generate_8d_report(cluster, all_findings)
        tsb_draft = self.capa.generate_tsb_draft(cluster, all_findings)
        execution_time_ms = round((time.time() - start_t) * 1000, 2)

        # Persist investigation
        prior_invs = db.query(Investigation).filter(Investigation.cluster_id == cluster_id).all()
        for p in prior_invs:
            if p.decision == "unreviewed":
                db.delete(p)
        db.commit()

        investigation = Investigation(
            cluster_id=cluster_id,
            status="completed",
            decision="unreviewed",
            reviewer="Reliability Engineer",
            summary_conclusion=summary_conclusion,
            confidence=overall_confidence,
            overall_classification=overall_classification,
            supporting_claims_count=len(supporting_claim_ids),
            contradicting_claims_count=len(contradicting_claim_ids),
            unknowns=unknowns,
            recommendations=recommendations,
            report_8d=report_8d,
            tsb_draft=tsb_draft,
            metrics_snapshot={
                "claim_count": cluster.claim_count,
                "alert_score": cluster.alert_score,
                "alert_level": cluster.alert_level,
                "growth_rate": cluster.growth_rate,
                "significance_score": cluster.significance_score,
                "cross_code_count": cluster.cross_code_count,
                "plant_count": cluster.plant_count
            },
            execution_time_ms=execution_time_ms
        )
        db.add(investigation)
        db.flush()

        for f in all_findings:
            f.investigation_id = investigation.id
            db.add(f)
        for t in all_tool_logs:
            t.investigation_id = investigation.id
            db.add(t)

        db.commit()
        db.refresh(investigation)

        yield {
            "event": "complete",
            "investigation_id": investigation.id,
            "confidence": overall_confidence,
            "overall_classification": overall_classification,
            "summary_conclusion": summary_conclusion,
            "report_8d": report_8d,
            "tsb_draft": tsb_draft,
            "execution_time_ms": execution_time_ms
        }
        return investigation

    def run_all_alerted_investigations(self, db: Session) -> List[Investigation]:
        """Runs investigations on all clusters with alert level HIGH or CRITICAL."""
        alerted_clusters = db.query(Cluster).filter(
            Cluster.cluster_index != -1,
            Cluster.alert_level.in_(["CRITICAL", "HIGH"])
        ).order_by(Cluster.alert_score.desc()).all()

        results = []
        for c in alerted_clusters:
            inv = self.run_investigation(db, c.id, force_recompute=True)
            results.append(inv)
        return results

orchestrator = InvestigationOrchestrator()
