import os
import random
from datetime import date, timedelta

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from ingest.claim_schema import ClaimInput
from narrator.templates import LANGUAGES, explain
from reasoner import audit, engine
from reasoner.kb import load_kb

KB = load_kb()
RANK = {"PASS": 0, "AT_RISK": 1, "WILL_FAIL": 2}
FACILITIES = [facility["id"] for facility in KB.facilities] + ["fac-99"]
SERVICES = [service["id"] for service in KB.services] + ["svc-XX-99"]
BASE_DAY = date(2026, 9, 1)

FUZZ = settings(
    max_examples=int(os.environ.get("FUZZ_EXAMPLES", "12")),
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@st.composite
def claims(draw):
    service_day = BASE_DAY + timedelta(days=draw(st.integers(0, 40)))
    lodging = service_day + timedelta(days=draw(st.integers(0, 14)))
    payload = {
        "claim_ref": f"clm-{draw(st.integers(1, 9999))}",
        "patient_token": f"pat-{draw(st.integers(1, 5))}",
        "facility_id": draw(st.sampled_from(FACILITIES)),
        "service_code": draw(st.sampled_from(SERVICES)),
        "fund": draw(st.sampled_from(["PHC", "SHIF", "ECCIF"])),
        "date_of_service": service_day.isoformat(),
        "amount_kes": draw(st.integers(1, 200_000)),
        "member_status": draw(st.sampled_from(["active", "inactive", "unknown"])),
        "emergency": draw(st.booleans()),
        "lodging_date": lodging.isoformat(),
    }
    for field, options in (
        ("preauth_ref", ["PA-1001", None]),
        ("referral_ref", ["REF-2002", None]),
        ("icd_code", ["O82", "K35.8", "J06.9", "C50.9", "N18.6", "B50.9", None]),
    ):
        value = draw(st.sampled_from(options))
        if value:
            payload[field] = value
    return ClaimInput.model_validate(payload).to_claim()


@st.composite
def histories(draw, claim_strategy=claims()):
    return draw(st.lists(claim_strategy, max_size=4))


@FUZZ
@given(claim=claims())
def test_engine_never_crashes_and_stays_within_bounds(claim):
    result = engine.check(claim)
    strength, confidence = result["truth_value"].values()
    assert result["verdict"] in RANK
    assert 0 <= strength <= 1 and 0 <= confidence <= 1
    assert len(result["trace"]) == 11
    assert 0 <= result["revenue_at_risk_kes"] <= claim["amount_kes"]
    if result["verdict"] == "PASS":
        assert result["revenue_at_risk_kes"] == 0
    if result["verdict"] == "WILL_FAIL":
        assert result["revenue_at_risk_kes"] == claim["amount_kes"]
    for step in result["trace"]:
        assert step["fact"] and ("stv" in step) == (step["result"] != "skip")


@FUZZ
@given(claim=claims())
def test_the_same_claim_always_gives_the_same_hash(claim):
    assert audit.trace_hash(engine.check(claim)) == audit.trace_hash(engine.check(claim))


@FUZZ
@given(claim=claims())
def test_a_verdict_is_a_pure_function_of_the_claim_and_history(claim):
    history = [
        {**claim, "claim_ref": f"old-{n}", "patient_token": claim["patient_token"]}
        for n in range(3)
    ]
    shuffled = history[:]
    random.Random(1).shuffle(shuffled)
    assert audit.trace_hash(engine.check(claim, history)) == audit.trace_hash(
        engine.check(claim, shuffled)
    )


@FUZZ
@given(claim=claims())
def test_every_offered_fix_really_repairs_its_rule(claim):
    result = engine.check(claim)
    for fix in result["fixes"]:
        patched = engine.check({**claim, **fix["patch"]})
        repaired = next(
            step for step in patched["trace"] if step["rule"].startswith(fix["rule"] + "-")
        )
        assert repaired["result"] == "pass"
        assert fix["flips_to"] == patched["verdict"]


@FUZZ
@given(claim=claims(), extra=st.integers(1, 100_000))
def test_billing_more_never_improves_the_verdict(claim, extra):
    low = engine.check(claim)
    high = engine.check({**claim, "amount_kes": claim["amount_kes"] + extra})
    assert RANK[high["verdict"]] >= RANK[low["verdict"]]


@FUZZ
@given(claim=claims())
def test_narration_renders_in_every_language(claim):
    result = engine.check(claim)
    for language in LANGUAGES:
        text = explain(KB, result, language)
        assert text.strip() and "{" not in text and "}" not in text


@FUZZ
@given(claim=claims())
def test_an_emergency_never_needs_preauthorisation_or_referral(claim):
    result = engine.check({**claim, "emergency": True, "preauth_ref": None, "referral_ref": None})
    by_rule = {step["rule"].split("-")[0]: step["result"] for step in result["trace"]}
    assert by_rule["R3"] in {"pass", "skip"} and by_rule["R11"] == "pass"


@pytest.mark.parametrize("seed", range(5))
def test_history_with_many_priors_stays_correct(seed):
    rng = random.Random(seed)
    claim = {
        "claim_ref": "clm-1",
        "patient_token": "pat-1",
        "facility_id": "fac-12",
        "service_code": "svc-DIA-01",
        "fund": "SHIF",
        "date_of_service": "2026-10-09",
        "amount_kes": 10650,
        "member_status": "active",
        "emergency": False,
        "preauth_ref": "PA-1",
        "referral_ref": "REF-1",
        "icd_code": "N18.6",
        "discharge_date": None,
        "lodging_date": "2026-10-10",
    }
    priors = [
        {
            "claim_ref": f"p{n}",
            "patient_token": "pat-1",
            "service_code": "svc-DIA-01",
            "date_of_service": (date(2026, 10, 9) - timedelta(days=rng.randint(1, 20))).isoformat(),
        }
        for n in range(30)
    ]
    inside = sum(
        1
        for prior in priors
        if (date(2026, 10, 9) - date.fromisoformat(prior["date_of_service"])).days < 7
    )
    expected = "fail" if inside >= 3 else "pass"
    result = engine.check(claim, priors)
    assert next(s for s in result["trace"] if s["rule"].startswith("R8-"))["result"] == expected
