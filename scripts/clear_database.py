import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal, engine, Base
from apps.api.models import Claim, FailureSignature, Embedding, Cluster, ClusterClaim, CodeMismatch, Feedback, DefectFingerprint, AnalysisRun, AuditLog

def clear_all_data():
    print("=" * 60)
    print("  WarrantyPatternMiner -- Database Reset & Clean Utility")
    print("=" * 60)
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        n_cc = db.query(ClusterClaim).delete()
        n_c = db.query(Cluster).delete()
        n_cm = db.query(CodeMismatch).delete()
        n_emb = db.query(Embedding).delete()
        n_sig = db.query(FailureSignature).delete()
        n_fb = db.query(Feedback).delete()
        n_fp = db.query(DefectFingerprint).delete()
        n_run = db.query(AnalysisRun).delete()
        n_log = db.query(AuditLog).delete()
        n_claims = db.query(Claim).delete()
        db.commit()

        print(f"[*] Deleted {n_claims} Claim records")
        print(f"[*] Deleted {n_sig} Failure Signature records")
        print(f"[*] Deleted {n_emb} Embedding records")
        print(f"[*] Deleted {n_cm} Code Mismatch records")
        print(f"[*] Deleted {n_c} Cluster records & {n_cc} Cluster-Claim mappings")
        print(f"[*] Deleted {n_fb} Feedback & {n_fp} Defect Fingerprints")
        print(f"[*] Deleted {n_run} Analysis Runs & {n_log} Audit Logs")
        print("\n[SUCCESS] SQLite database is now completely clean (0 claims, 0 clusters).")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to clear database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_data()
