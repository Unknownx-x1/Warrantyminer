import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sqlalchemy.orm import Session
from apps.api.models.claim import Claim, FailureSignature, Embedding

logger = logging.getLogger(__name__)

def build_semantic_text(claim: Claim, sig: Optional[FailureSignature]) -> str:
    parts = []
    if sig:
        if sig.component:
            # Component keywords upweighted
            parts.append(f"Component: {sig.component} {sig.component}")
        if sig.symptom:
            # Symptom keywords upweighted
            parts.append(f"Symptom: {sig.symptom} {sig.symptom}")
        if sig.condition:
            parts.append(f"Condition: {sig.condition}")
        if sig.inferred_failure:
            parts.append(f"Failure: {sig.inferred_failure}")
    parts.append(f"Narrative: {claim.narrative}")
    return " | ".join(parts)

def compute_embeddings_for_corpus(claims: List[Claim], signatures_map: Dict[str, FailureSignature]) -> Tuple[List[str], np.ndarray]:
    """
    Computes dense semantic representations for a collection of claims.
    Uses an n-gram TF-IDF + SVD semantic space normalized to unit length.
    """
    semantic_texts = []
    for claim in claims:
        sig = signatures_map.get(claim.id)
        stext = build_semantic_text(claim, sig)
        semantic_texts.append(stext)

    if not semantic_texts:
        return [], np.empty((0, 32))

    n_samples = len(semantic_texts)
    # Dimensionality for SVD
    n_components = min(40, max(8, n_samples - 1)) if n_samples > 2 else 2

    # Fit TF-IDF with character and word n-grams
    tfidf = TfidfVectorizer(
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.90,
        sublinear_tf=True
    )
    tfidf_matrix = tfidf.fit_transform(semantic_texts)

    if n_samples >= 5:
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        dense_vectors = svd.fit_transform(tfidf_matrix)
    else:
        dense_vectors = tfidf_matrix.toarray()

    # L2 unit normalization
    normalized_vectors = normalize(dense_vectors, norm="l2")
    return semantic_texts, normalized_vectors

def process_embeddings(db: Session, force: bool = False) -> int:
    """
    Generates and persists semantic embeddings for all claims in the database.
    """
    all_claims = db.query(Claim).all()
    if not all_claims:
        return 0

    if not force:
        existing_count = db.query(Embedding).count()
        if existing_count == len(all_claims):
            return 0

    all_signatures = db.query(FailureSignature).all()
    sig_map = {s.claim_id: s for s in all_signatures}

    semantic_texts, vectors = compute_embeddings_for_corpus(all_claims, sig_map)

    if force:
        db.query(Embedding).delete()
        db.commit()

    embeddings_to_add = []
    for idx, claim in enumerate(all_claims):
        vec_list = vectors[idx].tolist()
        emb_obj = Embedding(
            claim_id=claim.id,
            vector=vec_list,
            semantic_text=semantic_texts[idx],
            model_name="tfidf-svd-dense-v1"
        )
        embeddings_to_add.append(emb_obj)

    if embeddings_to_add:
        db.bulk_save_objects(embeddings_to_add)
        db.commit()

    logger.info(f"Generated and saved {len(embeddings_to_add)} claim embeddings.")
    return len(embeddings_to_add)
