import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.preprocessing import normalize
from sqlalchemy.orm import Session
import httpx

from apps.api.config import settings
from apps.api.models.claim import Claim, FailureSignature, Embedding

logger = logging.getLogger(__name__)

# Global model cache to avoid re-loading ONNX models on every invocation
_FASTEMBED_MODEL = None

def get_fastembed_model():
    """
    Initializes or returns cached FastEmbed TextEmbedding instance.
    Uses ONNX Runtime CPU execution for instant (<2ms/claim) inference.
    """
    global _FASTEMBED_MODEL
    if _FASTEMBED_MODEL is None:
        try:
            from fastembed import TextEmbedding
            model_name = settings.EMBEDDING_MODEL or "BAAI/bge-small-en-v1.5"
            if not model_name or "text-embedding" in model_name:
                model_name = "BAAI/bge-small-en-v1.5"
            logger.info(f"Initializing FastEmbed ONNX transformer with model: {model_name}")
            _FASTEMBED_MODEL = TextEmbedding(model_name=model_name)
        except Exception as e:
            logger.warning(f"FastEmbed initialization failed: {e}. Retrying with default BAAI/bge-small-en-v1.5...")
            try:
                from fastembed import TextEmbedding
                _FASTEMBED_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except Exception as e2:
                logger.warning(f"FastEmbed default initialization failed: {e2}. Will use fallback.")
                _FASTEMBED_MODEL = None
    return _FASTEMBED_MODEL

def build_semantic_text(claim: Claim, sig: Optional[FailureSignature]) -> str:
    """
    Constructs a rich semantic representation combining structured failure signatures
    and raw technician narratives.
    """
    parts = []
    if sig:
        if sig.component and sig.component != "unspecified component":
            parts.append(f"Component: {sig.component}")
        if sig.symptom and sig.symptom != "unspecified operational symptom":
            parts.append(f"Symptom: {sig.symptom}")
        if sig.condition and sig.condition != "normal operating conditions":
            parts.append(f"Condition: {sig.condition}")
        if sig.inferred_failure:
            parts.append(f"Failure: {sig.inferred_failure}")
    parts.append(f"Narrative: {claim.narrative}")
    return " | ".join(parts)

def _embed_via_fastembed(texts: List[str]) -> Optional[np.ndarray]:
    """Generates dense embeddings via FastEmbed ONNX Runtime."""
    model = get_fastembed_model()
    if model is None:
        return None
    try:
        raw_embs = list(model.embed(texts, batch_size=64))
        vectors = np.array(raw_embs, dtype=np.float32)
        return normalize(vectors, norm="l2")
    except Exception as e:
        logger.warning(f"FastEmbed inference error: {e}")
        return None

def _embed_via_ollama(texts: List[str]) -> Optional[np.ndarray]:
    """Generates dense embeddings via local Ollama HTTP API."""
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embed"
        model_name = "nomic-embed-text"
        vectors = []
        batch_size = 32
        with httpx.Client(timeout=30.0) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                resp = client.post(url, json={"model": model_name, "input": batch})
                if resp.status_code == 200:
                    vectors.extend(resp.json()["embeddings"])
                else:
                    return None
        arr = np.array(vectors, dtype=np.float32)
        return normalize(arr, norm="l2")
    except Exception as e:
        logger.warning(f"Ollama embedding failed: {e}")
        return None

def _embed_via_tfidf_svd(texts: List[str]) -> np.ndarray:
    """Fallback: TF-IDF + SVD count-based dimensional reduction."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    n_samples = len(texts)
    n_components = min(32, max(6, n_samples - 1)) if n_samples > 2 else 2
    max_df_val = 0.85 if n_samples >= 25 else 1.0

    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_df=max_df_val,
        sublinear_tf=True
    )
    tfidf_matrix = tfidf.fit_transform(texts)
    if n_samples >= 5:
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        dense_vectors = svd.fit_transform(tfidf_matrix)
    else:
        dense_vectors = tfidf_matrix.toarray()
    return normalize(dense_vectors, norm="l2")

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Computes unit-normalized dense embeddings for a list of arbitrary text strings.
    Uses FastEmbed ONNX -> Ollama -> TF-IDF Fallback.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    
    provider = settings.EMBEDDING_PROVIDER.lower()
    vectors = None

    if provider == "ollama" or (settings.USE_OLLAMA and provider != "fastembed"):
        vectors = _embed_via_ollama(texts)

    if vectors is None:
        vectors = _embed_via_fastembed(texts)

    if vectors is None:
        vectors = _embed_via_tfidf_svd(texts)

    return vectors

def embed_text(text: str) -> np.ndarray:
    """
    Computes a 1D unit-normalized dense vector for a single text string.
    """
    embs = embed_texts([text])
    if len(embs) > 0:
        return embs[0]
    return np.zeros(384, dtype=np.float32)

def compute_embeddings_for_corpus(
    claims: List[Claim], 
    signatures_map: Dict[str, FailureSignature]
) -> Tuple[List[str], np.ndarray, str]:
    """
    Computes dense semantic representations for a collection of claims using
    the best available provider (FastEmbed ONNX -> Ollama -> TF-IDF Fallback).
    Returns: (semantic_texts, normalized_vectors, model_name)
    """
    semantic_texts = []
    for claim in claims:
        sig = signatures_map.get(claim.id)
        stext = build_semantic_text(claim, sig)
        semantic_texts.append(stext)

    if not semantic_texts:
        return [], np.empty((0, 384)), "empty"

    provider = settings.EMBEDDING_PROVIDER.lower()
    vectors = None
    model_name = "fastembed:bge-small-en-v1.5"

    if provider == "ollama" or (settings.USE_OLLAMA and provider != "fastembed"):
        vectors = _embed_via_ollama(semantic_texts)
        if vectors is not None:
            model_name = "ollama:nomic-embed-text"

    if vectors is None:
        vectors = _embed_via_fastembed(semantic_texts)
        if vectors is not None:
            model_name = f"fastembed:{settings.EMBEDDING_MODEL}"

    if vectors is None:
        logger.warning("Neural embedding backends unavailable, falling back to TF-IDF+SVD")
        vectors = _embed_via_tfidf_svd(semantic_texts)
        model_name = "tfidf-svd-fallback"

    return semantic_texts, vectors, model_name

def process_embeddings(db: Session, force: bool = False) -> int:
    """
    Generates and persists semantic embeddings for all claims in the database.
    """
    all_claims = db.query(Claim).order_by(Claim.id).all()
    if not all_claims:
        return 0

    if not force:
        existing_count = db.query(Embedding).count()
        if existing_count == len(all_claims):
            return 0

    all_signatures = db.query(FailureSignature).all()
    sig_map = {s.claim_id: s for s in all_signatures}

    semantic_texts, vectors, model_name = compute_embeddings_for_corpus(all_claims, sig_map)

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
            model_name=model_name
        )
        embeddings_to_add.append(emb_obj)

    if embeddings_to_add:
        db.bulk_save_objects(embeddings_to_add)
        db.commit()

    logger.info(f"Generated and saved {len(embeddings_to_add)} claim embeddings using [{model_name}].")
    return len(embeddings_to_add)
