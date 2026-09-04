import io
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session
from apps.api.models.claim import Claim
from apps.api.schemas.claim import ClaimCreate

logger = logging.getLogger(__name__)

def parse_date_safely(date_val: Any) -> Optional[date]:
    if pd.isna(date_val) or date_val is None:
        return None
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    
    date_str = str(date_val).strip()
    # Try multiple standard date formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%Y%m%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    try:
        # Fallback to pandas timestamp parser
        parsed = pd.to_datetime(date_str)
        return parsed.date()
    except Exception:
        return None

def normalize_claim_record(raw: Dict[str, Any], source: str = "upload") -> Optional[Dict[str, Any]]:
    # Find claim_id or id
    claim_id = raw.get("claim_id") or raw.get("id") or raw.get("external_claim_id") or raw.get("Claim ID")
    if not claim_id or str(claim_id).strip() == "" or str(claim_id).lower() == "nan":
        return None
    claim_id = str(claim_id).strip()

    # Find date
    date_val = raw.get("date") or raw.get("claim_date") or raw.get("Date") or raw.get("Claim Date")
    parsed_date = parse_date_safely(date_val)
    if not parsed_date:
        # If no valid date, default to current date
        parsed_date = date.today()

    # Find narrative
    narrative = raw.get("narrative") or raw.get("narrative_text") or raw.get("Narrative") or raw.get("Complaint") or raw.get("technician_notes") or raw.get("description")
    if not narrative or str(narrative).strip() == "" or str(narrative).lower() == "nan":
        return None
    narrative = str(narrative).strip()

    # Find failure_code
    failure_code = raw.get("failure_code") or raw.get("code") or raw.get("Failure Code") or raw.get("structured_failure_code")
    if pd.isna(failure_code) or failure_code is None or str(failure_code).strip() == "" or str(failure_code).lower() == "nan":
        failure_code = "UNASSIGNED"
    else:
        failure_code = str(failure_code).strip().upper()

    # Find product_model
    product_model = raw.get("product_model") or raw.get("model") or raw.get("Product") or raw.get("Vehicle Model") or raw.get("product")
    if pd.isna(product_model) or product_model is None or str(product_model).lower() == "nan":
        product_model = "Standard Series"
    else:
        product_model = str(product_model).strip()

    # Find plant
    plant = raw.get("plant") or raw.get("Plant") or raw.get("location") or raw.get("facility")
    if pd.isna(plant) or plant is None or str(plant).lower() == "nan":
        plant = "Plant A"
    else:
        plant = str(plant).strip()

    return {
        "external_claim_id": claim_id,
        "claim_date": parsed_date,
        "product_model": product_model,
        "plant": plant,
        "failure_code": failure_code,
        "narrative": narrative,
        "source": source
    }

def ingest_claims_data(file_content: bytes, filename: str, db: Session) -> Tuple[int, int, List[str]]:
    """
    Ingests claims from CSV or JSON content.
    Returns: (inserted_count, updated_or_skipped_count, errors)
    """
    errors = []
    records = []
    
    try:
        if filename.endswith(".json") or file_content.strip().startswith(b"[") or file_content.strip().startswith(b"{"):
            raw_json = json.loads(file_content.decode("utf-8"))
            if isinstance(raw_json, dict):
                # If wrapped in key like 'claims' or 'data'
                if "claims" in raw_json:
                    records = raw_json["claims"]
                elif "data" in raw_json:
                    records = raw_json["data"]
                else:
                    records = [raw_json]
            elif isinstance(raw_json, list):
                records = raw_json
        else:
            # Assume CSV
            df = pd.read_csv(io.BytesIO(file_content))
            records = df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Failed to parse upload file {filename}: {e}")
        errors.append(f"File parsing error: {str(e)}")
        return 0, 0, errors

    inserted = 0
    skipped = 0

    # Fetch existing external_claim_ids to avoid duplicate conflict crashes
    existing_claim_ids = {c[0] for c in db.query(Claim.external_claim_id).all()}

    claims_to_add = []
    for idx, rec in enumerate(records):
        try:
            norm = normalize_claim_record(rec, source=filename)
            if not norm:
                skipped += 1
                continue
            
            ext_id = norm["external_claim_id"]
            if ext_id in existing_claim_ids:
                # Update existing or skip
                skipped += 1
                continue
            
            existing_claim_ids.add(ext_id)
            claim_obj = Claim(
                external_claim_id=norm["external_claim_id"],
                claim_date=norm["claim_date"],
                product_model=norm["product_model"],
                plant=norm["plant"],
                failure_code=norm["failure_code"],
                narrative=norm["narrative"],
                source=norm["source"]
            )
            claims_to_add.append(claim_obj)
            inserted += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            skipped += 1

    if claims_to_add:
        db.bulk_save_objects(claims_to_add)
        db.commit()

    logger.info(f"Ingestion completed: {inserted} inserted, {skipped} skipped, {len(errors)} errors.")
    return inserted, skipped, errors
