import csv
from pathlib import Path

import pytest

from ingest.claim_schema import ClaimInput
from reasoner import engine
from reasoner.kb import load_kb

from ..helpers import cs_claim, make_claim, prior

SYNTHETIC = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "claims.csv"


def test_every_rule_outcome_has_premises_and_the_other_way_round():
    kb = load_kb()
    expected = {
        f"{rule_id}.{key}"
        for rule_id, rule in kb.citations["rules"].items()
        for key in rule["messages"]
    }
    assert set(kb.premises) == expected


def test_a_failing_step_lists_the_atoms_it_matched():
    result = engine.check(cs_claim(), [])
    step = next(item for item in result["trace"] if item["rule"].startswith("R3-"))
    assert "(PreauthRequired svc-CS-01 SHIF)" in step["premises"]
    assert "(not (PreauthRef clm-104 $ref))" in step["premises"]


def test_a_passing_step_lists_the_fact_that_satisfied_it():
    step = next(
        item
        for item in engine.check(cs_claim(preauth_ref="PA-1"), [])["trace"]
        if item["rule"].startswith("R3-")
    )
    assert "(PreauthRef clm-104 PA-1)" in step["premises"]


def test_duplicate_premises_name_the_earlier_claim():
    history = [prior("clm-001", "2026-10-14")]
    step = next(
        item
        for item in engine.check(make_claim(), history)["trace"]
        if item["rule"].startswith("R8-")
    )
    assert any(atom.startswith("(Prior clm-001 pat-77 svc-OPD-01") for atom in step["premises"])


def test_every_step_of_every_synthetic_claim_has_premises():
    with SYNTHETIC.open() as handle:
        rows = list(csv.DictReader(handle))
    history = []
    for row in rows:
        claim = ClaimInput.model_validate({k: v for k, v in row.items() if v}).to_claim()
        result = engine.check(claim, history)
        history.append(claim)
        assert all(step["premises"] for step in result["trace"]), claim["claim_ref"]


def test_fix_search_does_not_pay_for_premises(monkeypatch):
    calls = []
    original = engine.premises_for
    monkeypatch.setattr(
        engine, "premises_for", lambda *a, **k: calls.append(1) or original(*a, **k)
    )
    engine.check(cs_claim(), [])
    assert len(calls) == 11


@pytest.mark.parametrize("rule_id", [f"R{n}" for n in range(1, 12)])
def test_the_rule_source_is_available(rule_id):
    assert f"(check-{rule_id.lower()} " in load_kb().rule_source(rule_id)
