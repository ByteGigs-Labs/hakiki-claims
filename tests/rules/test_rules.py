import pytest

from reasoner import engine
from tests.helpers import make_claim, prior, step

CASES = [
    ("R1", {}, "pass"),
    ("R1", {"member_status": "inactive"}, "fail"),
    ("R1", {"member_status": "unknown"}, "warn"),
    ("R2", {}, "pass"),
    ("R2", {"facility_id": "fac-09", "date_of_service": "2026-01-16"}, "pass"),
    ("R2", {"facility_id": "fac-09", "date_of_service": "2026-04-02"}, "fail"),
    (
        "R2",
        {"facility_id": "fac-12", "fund": "ECCIF", "service_code": "svc-ER-01", "amount_kes": 900},
        "pass",
    ),
    ("R2", {"facility_id": "fac-02", "fund": "SHIF"}, "fail"),
    ("R2", {"facility_id": "fac-99"}, "warn"),
    ("R3", {}, "pass"),
    ("R3", {"service_code": "svc-CS-01", "amount_kes": 45000}, "fail"),
    ("R3", {"service_code": "svc-CS-01", "amount_kes": 45000, "preauth_ref": "PA-1001"}, "pass"),
    ("R3", {"service_code": "svc-XX-99"}, "skip"),
    ("R4", {}, "pass"),
    ("R4", {"service_code": "svc-ONC-01", "amount_kes": 70000}, "fail"),
    ("R4", {"service_code": "svc-XX-99"}, "fail"),
    ("R5", {}, "pass"),
    ("R5", {"service_code": "svc-MRI-01", "amount_kes": 17000}, "fail"),
    ("R5", {"service_code": "svc-MRI-01", "facility_id": "fac-15", "amount_kes": 17000}, "pass"),
    ("R5", {"facility_id": "fac-99"}, "skip"),
    ("R6", {}, "pass"),
    ("R6", {"amount_kes": 800}, "pass"),
    ("R6", {"amount_kes": 800.5}, "fail"),
    ("R6", {"service_code": "svc-ONC-01", "fund": "SHIF", "amount_kes": 70000}, "skip"),
    ("R8", {}, "pass"),
]


@pytest.mark.parametrize(("rule", "overrides", "outcome"), CASES)
def test_rule_outcome(rule, overrides, outcome):
    result = engine.check(make_claim(**overrides))
    assert step(result, rule)["result"] == outcome


def test_duplicate_claim_for_same_patient_service_and_date_fails():
    result = engine.check(make_claim(claim_ref="clm-2"), [prior("clm-1", "2026-10-14")])
    assert step(result, "R8")["result"] == "fail"
    assert "clm-1" in step(result, "R8")["fact"]


def test_same_claim_reference_is_not_a_duplicate_of_itself():
    result = engine.check(make_claim(), [prior("clm-104", "2026-10-14")])
    assert step(result, "R8")["result"] == "pass"


def test_other_patients_and_services_do_not_count():
    history = [
        prior("clm-1", "2026-10-14", patient="pat-99"),
        prior("clm-2", "2026-10-14", service="svc-LAB-01"),
        prior("clm-3", "2026-10-13"),
    ]
    assert step(engine.check(make_claim(claim_ref="clm-9"), history), "R8")["result"] == "pass"


def test_frequency_limit_applies_inside_the_window_only():
    dental = {"service_code": "svc-DEN-01", "amount_kes": 2800, "facility_id": "fac-03"}
    history = [prior("a", "2026-02-10", "svc-DEN-01"), prior("b", "2026-06-15", "svc-DEN-01")]
    assert step(engine.check(make_claim(**dental), history), "R8")["result"] == "fail"
    stale = [prior("a", "2025-09-01", "svc-DEN-01"), prior("b", "2026-06-15", "svc-DEN-01")]
    assert step(engine.check(make_claim(**dental), stale), "R8")["result"] == "pass"


def test_future_priors_do_not_count_against_frequency():
    dental = {"service_code": "svc-DEN-01", "amount_kes": 2800, "facility_id": "fac-03"}
    history = [prior("a", "2026-10-16", "svc-DEN-01"), prior("b", "2026-10-17", "svc-DEN-01")]
    assert step(engine.check(make_claim(**dental), history), "R8")["result"] == "pass"
