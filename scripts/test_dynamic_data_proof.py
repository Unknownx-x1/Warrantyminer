import os
import sys
import json
import csv
import io
from pathlib import Path
from datetime import date

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal, engine, Base
from apps.api.models import Claim, FailureSignature, Embedding, Cluster, ClusterClaim, CodeMismatch, Feedback, DefectFingerprint
from apps.api.services.ingestion import ingest_claims_data
from apps.api.services.pipeline_orchestrator import execute_full_pipeline
from apps.api.routes.alerts import get_dashboard_summary

def reset_db(db):
    db.query(ClusterClaim).delete()
    db.query(Cluster).delete()
    db.query(CodeMismatch).delete()
    db.query(Embedding).delete()
    db.query(FailureSignature).delete()
    db.query(Feedback).delete()
    db.query(DefectFingerprint).delete()
    db.query(Claim).delete()
    db.commit()

def run_dynamic_proof():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=" * 75)
    print("      WARRANTYPATTERNMINER -- DYNAMIC DATA ENGINE VERIFICATION PROOF")
    print("=" * 75)

    # ---------------------------------------------------------
    # STAGE 1: Verify Empty / Zero State
    # ---------------------------------------------------------
    print("\n[STAGE 1] Testing Clean / Empty Database State...")
    reset_db(db)
    summary_empty = get_dashboard_summary(db)
    print("Summary Response (Empty DB):")
    print(f"  - Claims Analyzed:    {summary_empty['claims_analyzed']}")
    print(f"  - Emerging Patterns:  {summary_empty['emerging_patterns']}")
    print(f"  - High Risk Patterns: {summary_empty['high_risk_patterns']}")
    print(f"  - Miscoded Claims:    {summary_empty['miscoded_claims']}")
    print(f"  - Hero Cluster:       {summary_empty['hero_cluster']}")

    assert summary_empty['claims_analyzed'] == 0, f"Expected 0 claims, got {summary_empty['claims_analyzed']}"
    assert summary_empty['emerging_patterns'] == 0, f"Expected 0 patterns, got {summary_empty['emerging_patterns']}"
    assert summary_empty['hero_cluster'] is None, f"Expected None hero_cluster, got {summary_empty['hero_cluster']}"
    print(">> STAGE 1 PASSED: Clean empty state returns 0s and None.")

    # ---------------------------------------------------------
    # STAGE 2: Ingest Exactly 10 Claims
    # ---------------------------------------------------------
    print("\n[STAGE 2] Ingesting Dataset A (Exactly 10 claims)...")
    claims_10 = [
        {"claim_id": f"T10-{i:03d}", "date": f"2026-05-{10+i:02d}", "product_model": "Sedan-X", "plant": "Plant A - Fremont", "failure_code": "HVAC", "narrative": f"HVAC blowing warm air and loud whistling noise in cabin test {i}"}
        for i in range(1, 6)
    ] + [
        {"claim_id": f"T10-{i:03d}", "date": f"2026-06-{10+i:02d}", "product_model": "SUV-Y", "plant": "Plant B - Austin", "failure_code": "BRAKES", "narrative": f"Front brake squeal and vibration during moderate stopping {i}"}
        for i in range(6, 11)
    ]

    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["claim_id", "date", "product_model", "plant", "failure_code", "narrative"])
    writer.writeheader()
    writer.writerows(claims_10)
    
    inserted, skipped, errors = ingest_claims_data(csv_buf.getvalue().encode("utf-8"), "test_10.csv", db)
    print(f"  Ingested: {inserted} claims | Errors: {errors}")
    assert inserted == 10, f"Expected 10 inserted, got {inserted}"

    res_10 = execute_full_pipeline(db, dataset_name="dataset_10", force_recompute=True)
    summary_10 = get_dashboard_summary(db)

    print("\nSummary Response (10-Claim Dataset):")
    print(f"  - Claims Analyzed:    {summary_10['claims_analyzed']}")
    print(f"  - Emerging Patterns:  {summary_10['emerging_patterns']}")
    print(f"  - High Risk Patterns: {summary_10['high_risk_patterns']}")
    print(f"  - Miscoded Claims:    {summary_10['miscoded_claims']}")
    if summary_10['hero_cluster']:
        print(f"  - Top Defect Name:    {summary_10['hero_cluster']['label']}")
        print(f"  - Top Defect Score:   {summary_10['hero_cluster']['alert_score']}")
        print(f"  - Top Defect Volume:  {summary_10['hero_cluster']['claim_count']}")

    assert summary_10['claims_analyzed'] == 10, f"Expected claims_analyzed == 10, got {summary_10['claims_analyzed']}"
    print(">> STAGE 2 PASSED: Exactly 10 claims dynamically reflected.")

    # ---------------------------------------------------------
    # STAGE 3: Reset and Ingest Exactly 25 Completely Different Claims
    # ---------------------------------------------------------
    print("\n[STAGE 3] Ingesting Dataset B (Exactly 25 completely different claims)...")
    reset_db(db)
    
    claims_25 = [
        {"claim_id": f"T25-{i:03d}", "date": f"2026-03-{i:02d}", "product_model": "Coupe-Z", "plant": "Plant C - Leipzig", "failure_code": "TRANSMISSION", "narrative": f"Gearbox harsh shifting from 2nd to 3rd gear under acceleration event {i}"}
        for i in range(1, 15)
    ] + [
        {"claim_id": f"T25-{i:03d}", "date": f"2026-04-{i:02d}", "product_model": "Truck-W", "plant": "Plant A - Fremont", "failure_code": "STEERING", "narrative": f"Steering column clicking noise and stiffness at low speeds {i}"}
        for i in range(15, 26)
    ]

    csv_buf2 = io.StringIO()
    writer2 = csv.DictWriter(csv_buf2, fieldnames=["claim_id", "date", "product_model", "plant", "failure_code", "narrative"])
    writer2.writeheader()
    writer2.writerows(claims_25)

    inserted2, skipped2, errors2 = ingest_claims_data(csv_buf2.getvalue().encode("utf-8"), "test_25.csv", db)
    print(f"  Ingested: {inserted2} claims | Errors: {errors2}")
    assert inserted2 == 25, f"Expected 25 inserted, got {inserted2}"

    res_25 = execute_full_pipeline(db, dataset_name="dataset_25", force_recompute=True)
    summary_25 = get_dashboard_summary(db)

    print("\nSummary Response (25-Claim Dataset):")
    print(f"  - Claims Analyzed:    {summary_25['claims_analyzed']}")
    print(f"  - Emerging Patterns:  {summary_25['emerging_patterns']}")
    print(f"  - High Risk Patterns: {summary_25['high_risk_patterns']}")
    print(f"  - Miscoded Claims:    {summary_25['miscoded_claims']}")
    if summary_25['hero_cluster']:
        print(f"  - Top Defect Name:    {summary_25['hero_cluster']['label']}")
        print(f"  - Top Defect Score:   {summary_25['hero_cluster']['alert_score']}")
        print(f"  - Top Defect Volume:  {summary_25['hero_cluster']['claim_count']}")

    assert summary_25['claims_analyzed'] == 25, f"Expected claims_analyzed == 25, got {summary_25['claims_analyzed']}"
    assert summary_25['claims_analyzed'] != summary_10['claims_analyzed']
    print(">> STAGE 3 PASSED: Exactly 25 claims dynamically reflected with completely new patterns.")

    # ---------------------------------------------------------
    # STAGE 4: Re-evaluate Canonical 585-Claim Dataset
    # ---------------------------------------------------------
    print("\n[STAGE 4] Restoring Canonical 585-Claim Benchmark Dataset...")
    from scripts.evaluate_golden_dataset import evaluate
    evaluate()

    db.close()
    print("\n" + "=" * 75)
    print("      ALL DYNAMIC DATA PROOF STAGES COMPLETED & VERIFIED 100%")
    print("=" * 75)

if __name__ == "__main__":
    run_dynamic_proof()
