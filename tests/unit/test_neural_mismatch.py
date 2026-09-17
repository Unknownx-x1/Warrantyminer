import pytest
from apps.api.services.mismatch import evaluate_code_mismatch

def test_cross_domain_contradiction_detection():
    res = evaluate_code_mismatch(
        assigned_code='ELECTRICAL-NFF',
        component='front-left suspension',
        symptom='clunking noise',
        narrative='Customer reports severe front-left suspension clunk over speed bumps. Replaced worn lower ball joint.'
    )
    assert res['is_mismatch'] == 1
    assert res['mismatch_severity'] in ('HIGH', 'MEDIUM')
    assert res['mismatch_score'] >= 0.60
    assert 'Suspension' in res['inferred_category']
    assert 'contradicts' in res['reason'].lower() or 'misclassified' in res['inferred_category'].lower()

def test_generic_catchall_concealment_detection():
    res = evaluate_code_mismatch(
        assigned_code='OTHER',
        component='front brake assembly',
        symptom='vibration / shudder',
        narrative='Brake pedal pulsates heavily during highway stops; front brake rotors severely warped.'
    )
    assert res['is_mismatch'] == 1
    assert res['mismatch_score'] >= 0.50
    assert 'Brak' in res['inferred_category']

def test_code_agreement_detection():
    # 1. Electrical agreement
    res1 = evaluate_code_mismatch(
        assigned_code='ELECTRICAL',
        component='infotainment / display',
        symptom='screen flickering',
        narrative='Center touchscreen infotainment display flickers intermittently when Apple CarPlay is connected.'
    )
    assert res1['is_mismatch'] == 0
    assert res1['mismatch_severity'] == 'NORMAL'
    assert res1['mismatch_score'] < 0.45

    # 2. Suspension agreement
    res2 = evaluate_code_mismatch(
        assigned_code='SUSPENSION',
        component='front suspension',
        symptom='knocking noise',
        narrative='Front suspension strut knocking over potholes and rough pavement.'
    )
    assert res2['is_mismatch'] == 0
    assert res2['mismatch_severity'] == 'NORMAL'
    assert res2['mismatch_score'] < 0.30
