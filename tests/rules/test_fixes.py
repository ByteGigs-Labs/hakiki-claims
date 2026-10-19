from reasoner import engine
from tests.helpers import make_claim, prior


def fix_for(result: dict, rule: str) -> dict:
    return next(f for f in result["fixes"] if f["rule"] == rule)


def apply(claim: dict, fix: dict) -> dict:
    return {**claim, **fix["patch"]}


def test_missing_preauth_fix_flips_to_pass_when_applied():
    claim = make_claim(service_code="svc-CS-01", amount_kes=45000)
    fix = fix_for(engine.check(claim), "R3")
    assert (fix["flips_to"], fix["requires_input"]) == ("PASS", True)
    assert engine.check(apply(claim, fix))["verdict"] == "PASS"


def test_over_cap_fix_reduces_amount_to_the_tariff():
    claim = make_claim(amount_kes=1500)
    fix = fix_for(engine.check(claim), "R6")
    assert fix["patch"] == {"amount_kes": 800}
    assert fix["action"] == "Reduce the billed amount to the KES 800 tariff"
    assert engine.check(apply(claim, fix))["verdict"] == "PASS"


def test_inactive_member_fix_requires_input_and_flips_to_pass():
    claim = make_claim(member_status="inactive")
    fix = fix_for(engine.check(claim), "R1")
    assert fix["requires_input"] is True
    assert engine.check(apply(claim, fix))["verdict"] == "PASS"


def test_level_fix_points_to_a_contracted_qualifying_facility():
    claim = make_claim(service_code="svc-MRI-01", amount_kes=17000, preauth_ref="PA-9001")
    fix = fix_for(engine.check(claim), "R5")
    assert fix["patch"] == {"facility_id": "fac-15"}
    assert engine.check(apply(claim, fix))["verdict"] == "PASS"


def test_every_failing_rule_gets_a_fix_even_when_one_alone_is_not_enough():
    claim = make_claim(service_code="svc-CS-01", amount_kes=70000)
    result = engine.check(claim)
    assert {f["rule"] for f in result["fixes"]} == {"R3", "R6"}
    assert {f["flips_to"] for f in result["fixes"]} == {"WILL_FAIL"}


def test_applying_all_fixes_together_reaches_pass():
    claim = make_claim(service_code="svc-CS-01", amount_kes=70000)
    patched = claim
    for fix in engine.check(claim)["fixes"]:
        patched = apply(patched, fix)
    assert engine.check(patched)["verdict"] == "PASS"


def test_each_fix_reports_the_verdict_it_reaches_alone():
    claim = make_claim(service_code="svc-CS-01", amount_kes=70000)
    for fix in engine.check(claim)["fixes"]:
        assert fix["flips_to"] == engine.check(apply(claim, fix))["verdict"]


def test_duplicates_and_contract_failures_have_no_edit_fix():
    result = engine.check(make_claim(claim_ref="clm-2"), [prior("clm-1", "2026-10-14")])
    assert result["verdict"] == "WILL_FAIL" and result["fixes"] == []
