import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal, engine, Base
from apps.api.services.pipeline_orchestrator import execute_full_pipeline

def run():
    print("--- Executing WarrantyPatternMiner Analytical Pipeline ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        results = execute_full_pipeline(
            db=db,
            dataset_name="canonical_warranty_claims_v1",
            force_recompute=True
        )
        print(f"Pipeline status: {results['status']}")
        print(f"Total claims processed: {results['total_claims']}")
        print(f"Semantic clusters discovered: {results['clusters_found']}")
        print(f"Critical alerts flagged: {results['alerts_critical']}")
        print(f"High-priority alerts flagged: {results['alerts_high']}")
        print(f"Mismatches detected: {results['mismatches_detected']}")
        print(f"Execution time: {results['processing_time_ms']} ms")
    finally:
        db.close()

if __name__ == "__main__":
    run()
