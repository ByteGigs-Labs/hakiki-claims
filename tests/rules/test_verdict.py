import pytest

from reasoner import engine
from tests.helpers import make_claim, step


def test_clean_claim_passes_with_zero_revenue_at_risk():
    result = engine.check(make_claim())
    assert (result["verdict"], result["revenue_at_risk_kes"], result["fixes"]) == ("PASS", 0, [])
    assert result["truth_value"] == {"strength": 1.0, "confidence": 0.85}


def test_missing_preauth_will_fail_with_the_readme_example_values():
    result = engine.check(make_claim(service_code="svc-CS-01", amount_kes=45000))
    assert result["verdict"] == "WILL_FAIL"
    assert result["truth_value"] == {"strength": 0.95, "confidence": 0.92}
    assert result["revenue_at_risk_kes"] == 45000
    assert result["rulebook_version"] == "sha-rules-2026.10.0"


def test_unconfirmed_membership_is_at_risk_with_partial_revenue_at_risk():
    result = engine.check(make_claim(member_status="unknown", amount_kes=800))
    assert result["verdict"] == "AT_RISK"
    assert result["revenue_at_risk_kes"] == pytest.approx(480)


def test_several_failures_combine_with_noisy_or():
    result = engine.check(make_claim(service_code="svc-CS-01", amount_kes=70000))
    assert result["verdict"] == "WILL_FAIL"
    assert result["truth_value"]["strength"] == pytest.approx(1 - 0.05 * 0.1, abs=1e-4)
    assert result["truth_value"]["confidence"] == 0.85


def test_trace_is_ordered_and_cited():
    result = engine.check(make_claim())
    assert [s["step"] for s in result["trace"]] == list(range(1, 8))
    assert [s["rule"].split("-")[0] for s in result["trace"]] == [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R8",
    ]
    assert all(s["citation"].startswith("kb/citations.json#R") for s in result["trace"])


def test_skipped_steps_carry_no_truth_value():
    skipped = step(engine.check(make_claim(service_code="svc-XX-99")), "R3")
    assert skipped["result"] == "skip" and "stv" not in skipped


def test_unknown_service_cannot_pass():
    assert engine.check(make_claim(service_code="svc-XX-99"))["verdict"] == "WILL_FAIL"


def test_trace_facts_read_like_sentences_with_the_claim_numbers():
    result = engine.check(make_claim(amount_kes=1200))
    assert step(result, "R6")["fact"] == "Billed KES 1,200 exceeds the KES 800 tariff."


def test_claim_reference_with_metta_syntax_is_refused():
    with pytest.raises(ValueError):
        engine.check({**make_claim(), "claim_ref": "x) (Result R1 pass"})
