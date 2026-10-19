import pytest

from reasoner import engine
from tests.helpers import make_claim, prior, step

CS = {"service_code": "svc-CS-01", "amount_kes": 45000, "icd_code": "O82"}

CASES = [
    ("R1", {}, "pass"),
    ("R1", {"member_status": "inactive"}, "fail"),
    ("R1", {"member_status": "unknown"}, "warn"),
    ("R2", {}, "pass"),
    (
        "R2",
        {
            "facility_id": "fac-09",
            "fund": "PHC",
            "date_of_service": "2026-01-16",
            "lodging_date": "2026-01-17",
        },
        "pass",
    ),
    (
        "R2",
        {
            "facility_id": "fac-09",
            "fund": "PHC",
            "date_of_service": "2026-04-02",
            "lodging_date": "2026-04-03",
        },
        "fail",
    ),
    (
        "R2",
        {"facility_id": "fac-12", "fund": "ECCIF", "service_code": "svc-ER-01", "amount_kes": 900},
        "pass",
    ),
    ("R2", {"facility_id": "fac-03", "fund": "SHIF"}, "fail"),
    ("R2", {"facility_id": "fac-99"}, "warn"),
    ("R3", {}, "pass"),
    ("R3", CS, "fail"),
    ("R3", {**CS, "preauth_ref": "PA-1001"}, "pass"),
    ("R3", {**CS, "fund": "PHC", "facility_id": "fac-03", "amount_kes": 30000}, "pass"),
    ("R3", {**CS, "emergency": True}, "pass"),
    ("R3", {"service_code": "svc-XX-99"}, "skip"),
    ("R4", {}, "pass"),
    ("R4", {"service_code": "svc-ONC-01", "amount_kes": 70000}, "fail"),
    ("R4", {"service_code": "svc-XX-99"}, "fail"),
    ("R5", {}, "pass"),
    (
        "R5",
        {"service_code": "svc-ONC-01", "fund": "ECCIF", "amount_kes": 76000, "preauth_ref": "PA-9"},
        "fail",
    ),
    (
        "R5",
        {
            "service_code": "svc-ONC-01",
            "fund": "ECCIF",
            "facility_id": "fac-15",
            "amount_kes": 76000,
            "preauth_ref": "PA-9",
        },
        "pass",
    ),
    (
        "R5",
        {"service_code": "svc-OPD-01", "fund": "PHC", "facility_id": "fac-02", "amount_kes": 900},
        "pass",
    ),
    ("R5", {"facility_id": "fac-99"}, "skip"),
    ("R5", {"service_code": "svc-OPD-01", "fund": "ECCIF"}, "skip"),
    ("R6", {}, "pass"),
    ("R6", {"amount_kes": 1200}, "pass"),
    ("R6", {"amount_kes": 1200.5}, "fail"),
    ("R6", {"service_code": "svc-ONC-01", "fund": "SHIF", "amount_kes": 70000}, "skip"),
    ("R7", {}, "pass"),
    ("R7", {"icd_code": None}, "warn"),
    ("R8", {}, "pass"),
    ("R9", {}, "pass"),
    ("R9", {"icd_code": None}, "skip"),
    ("R9", CS, "pass"),
    ("R9", {**CS, "icd_code": "K35.8"}, "warn"),
    ("R9", {"service_code": "svc-DEN-01", "amount_kes": 3000, "icd_code": "K02.1"}, "pass"),
    ("R9", {"service_code": "svc-DEN-01", "amount_kes": 3000, "icd_code": "O82"}, "warn"),
    (
        "R9",
        {
            "service_code": "svc-ONC-01",
            "fund": "ECCIF",
            "facility_id": "fac-15",
            "amount_kes": 1,
            "icd_code": "D32.9",
        },
        "pass",
    ),
    ("R10", {}, "pass"),
    ("R10", {"lodging_date": "2026-10-21"}, "pass"),
    ("R10", {"lodging_date": "2026-10-22"}, "warn"),
    ("R10", {"discharge_date": "2026-10-18", "lodging_date": "2026-10-19"}, "pass"),
    ("R10", {"discharge_date": "2026-10-14", "lodging_date": "2026-10-19"}, "pass"),
    ("R11", {}, "pass"),
    ("R11", {"referral_ref": None}, "warn"),
    ("R11", {"referral_ref": None, "emergency": True}, "pass"),
    ("R11", {"referral_ref": None, "service_code": "svc-ER-01", "amount_kes": 900}, "pass"),
    (
        "R11",
        {"referral_ref": None, "fund": "PHC", "facility_id": "fac-12", "amount_kes": 900},
        "pass",
    ),
]


@pytest.mark.parametrize(("rule", "overrides", "outcome"), CASES)
def test_rule_outcome(rule, overrides, outcome):
    result = engine.check(make_claim(**overrides))
    assert step(result, rule)["result"] == outcome


def test_late_lodging_is_a_risk_not_a_certain_failure():
    result = engine.check(make_claim(lodging_date="2026-10-30"))
    assert result["verdict"] == "AT_RISK"
    assert step(result, "R10")["fact"] == "Lodged 16 days after discharge, beyond the 7-day window."


def test_discharge_date_moves_the_lodging_clock():
    result = engine.check(make_claim(discharge_date="2026-10-17", lodging_date="2026-10-19"))
    assert step(result, "R10")["fact"].startswith("Lodged 2 days")


def test_pass_on_a_published_tariff_is_more_confident_than_on_a_placeholder():
    verified = engine.check(
        make_claim(
            service_code="svc-CS-01",
            fund="PHC",
            facility_id="fac-03",
            amount_kes=30000,
            icd_code="O82",
        )
    )
    illustrative = engine.check(make_claim(amount_kes=1200))
    assert step(verified, "R6")["stv"] == [1.0, 0.9]
    assert step(illustrative, "R6")["stv"] == [1.0, 0.6]
    assert step(verified, "R6")["values"]["basis"] == "verified"
    assert step(illustrative, "R6")["values"]["basis"] == "illustrative"


def test_over_a_published_tariff_fails_with_higher_confidence():
    result = engine.check(
        make_claim(
            service_code="svc-CS-01",
            fund="PHC",
            facility_id="fac-03",
            amount_kes=35000,
            icd_code="O82",
        )
    )
    assert step(result, "R6")["result"] == "fail"
    assert step(result, "R6")["stv"] == [0.9, 0.85]
    assert step(result, "R6")["fact"] == "Billed KES 35,000 exceeds the KES 30,000 tariff."


def test_emergency_flag_waives_preauthorisation_and_referral_together():
    result = engine.check(make_claim(**CS, referral_ref=None, emergency=True))
    assert (step(result, "R3")["result"], step(result, "R11")["result"]) == ("pass", "pass")
    assert result["verdict"] == "PASS"


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


DENTAL = {"service_code": "svc-DEN-01", "amount_kes": 2800, "icd_code": "K02.1"}


def test_frequency_limit_applies_inside_the_window_only():
    history = [prior("a", "2026-02-10", "svc-DEN-01"), prior("b", "2026-06-15", "svc-DEN-01")]
    assert step(engine.check(make_claim(**DENTAL), history), "R8")["result"] == "fail"
    stale = [prior("a", "2025-09-01", "svc-DEN-01"), prior("b", "2026-06-15", "svc-DEN-01")]
    assert step(engine.check(make_claim(**DENTAL), stale), "R8")["result"] == "pass"


def test_future_priors_do_not_count_against_frequency():
    history = [prior("a", "2026-10-16", "svc-DEN-01"), prior("b", "2026-10-17", "svc-DEN-01")]
    assert step(engine.check(make_claim(**DENTAL), history), "R8")["result"] == "pass"
