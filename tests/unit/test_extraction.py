import pytest
from apps.api.services.extraction import extract_signature_rule_based

def test_extract_suspension_clunk():
    narrative = "Customer reports clunking noise from front left when driving over rough roads."
    sig = extract_signature_rule_based(narrative)
    
    assert sig["component"] == "front-left suspension"
    assert sig["symptom"] == "clunking / knocking noise"
    assert sig["condition"] == "rough roads / uneven surface"
    assert sig["confidence"] >= 0.85
    assert "bushing" in sig["inferred_failure"] or "suspension" in sig["inferred_failure"]

def test_extract_brake_squeak():
    narrative = "Technician found brake rotor squeal under gentle braking."
    sig = extract_signature_rule_based(narrative)
    
    assert "brake" in sig["component"]
    assert "squeal" in sig["symptom"]
    assert "braking" in sig["condition"]

def test_extract_electrical_screen():
    narrative = "Center infotainment touchscreen went black and rebooted spontaneously."
    sig = extract_signature_rule_based(narrative)
    
    assert "infotainment" in sig["component"]
    assert "intermittent" in sig["symptom"]
