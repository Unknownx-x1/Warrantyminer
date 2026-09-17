import pytest
import numpy as np
from apps.api.models.claim import Claim, FailureSignature
from apps.api.services.embeddings import compute_embeddings_for_corpus, build_semantic_text, get_fastembed_model
from apps.api.services.clustering import run_density_clustering, calculate_cluster_coherence
from sklearn.metrics.pairwise import cosine_similarity

def test_fastembed_model_initialization():
    model = get_fastembed_model()
    assert model is not None

def test_compute_embeddings_for_corpus_shape_and_norm():
    claims = [
        Claim(id='1', narrative='Technician notes front-left suspension clunk over speed bumps.'),
        Claim(id='2', narrative='Front suspension knocks when driving over potholes.'),
        Claim(id='3', narrative='Air conditioning compressor fails to blow cold air.')
    ]
    sigs = {
        '1': FailureSignature(claim_id='1', component='suspension', symptom='clunk'),
        '2': FailureSignature(claim_id='2', component='suspension', symptom='knock'),
        '3': FailureSignature(claim_id='3', component='hvac', symptom='no cooling')
    }

    stexts, vectors, model_name = compute_embeddings_for_corpus(claims, sigs)
    assert len(stexts) == 3
    assert vectors.shape == (3, 384)
    assert 'fastembed' in model_name or 'ollama' in model_name or 'tfidf' in model_name

    # Verify L2 Unit Normalization (norms == 1.0)
    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)

def test_semantic_discrimination():
    claims = [
        Claim(id='1', narrative='Rear differential whining sound under deceleration from 50mph.'),
        Claim(id='2', narrative='High pitch rear axle gear whine when easing off accelerator.'),
        Claim(id='3', narrative='Infotainment navigation touchscreen is black and unresponsive.')
    ]
    sigs = {}
    _, vectors, _ = compute_embeddings_for_corpus(claims, sigs)

    sim_related = float(np.dot(vectors[0], vectors[1]))
    sim_unrelated = float(np.dot(vectors[0], vectors[2]))

    # Semantic similarity of related failure must be significantly higher than unrelated
    assert sim_related > sim_unrelated
    assert sim_related >= 0.65
    assert sim_unrelated < 0.60

def test_neural_clustering_and_coherence():
    # 6 suspension claims and 6 HVAC claims
    susp_claims = [
        Claim(id=f'S{i}', narrative=f'Front suspension rattle and strut knocking on bumpy roads {i}.')
        for i in range(6)
    ]
    hvac_claims = [
        Claim(id=f'H{i}', narrative=f'Climate control AC blower motor squeal and blowing warm air {i}.')
        for i in range(6)
    ]
    all_claims = susp_claims + hvac_claims
    _, vectors, _ = compute_embeddings_for_corpus(all_claims, {})

    labels, probs = run_density_clustering(vectors, min_cluster_size=4, min_samples=2)
    assert len(labels) == 12

    # Verify coherence calculation
    susp_coherence = calculate_cluster_coherence(vectors[:6])
    hvac_coherence = calculate_cluster_coherence(vectors[6:])
    mixed_coherence = calculate_cluster_coherence(vectors)

    assert susp_coherence >= 0.70
    assert hvac_coherence >= 0.70
    assert mixed_coherence < susp_coherence
