import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal, engine, Base
from apps.api.models import Claim
from apps.api.services.ingestion import ingest_claims_data
from scripts.generate_demo_data import main as generate_data

def seed():
    print("Ensuring canonical demo data exists...")
    generate_data()

    csv_path = BASE_DIR / "data" / "raw" / "canonical_warranty_claims.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return

    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        with open(csv_path, "rb") as f:
            content = f.read()

        print(f"Ingesting claims from {csv_path.name}...")
        inserted, skipped, errors = ingest_claims_data(content, "canonical_warranty_claims.csv", db)
        print(f"Ingestion results: {inserted} inserted, {skipped} skipped, {len(errors)} errors.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
