import csv
from pathlib import Path

import pytest

from ingest.claim_schema import ClaimInput
from reasoner import audit, engine

SYNTHETIC = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def load_rows(name: str) -> list[dict]:
    with (SYNTHETIC / name).open() as handle:
        return list(csv.DictReader(handle))


def replay() -> list[tuple[dict, dict]]:
    history, outcomes = [], []
    for row in load_rows("claims.csv"):
        claim = ClaimInput.model_validate({k: v for k, v in row.items() if v}).to_claim()
        outcomes.append((claim, engine.check(claim, history)))
        history.append(claim)
    return outcomes


@pytest.fixture(scope="module")
def outcomes():
    return replay()


def test_every_synthetic_claim_matches_expected_verdict_and_failing_rules(outcomes):
    expected = {row["claim_ref"]: row for row in load_rows("expected.csv")}
    for claim, result in outcomes:
        failing = sorted(
            s["rule"].split("-")[0] for s in result["trace"] if s["result"] in {"fail", "warn"}
        )
        want = expected[claim["claim_ref"]]
        assert result["verdict"] == want["verdict"], claim["claim_ref"]
        assert failing == sorted(filter(None, want["failing_rules"].split(";"))), claim["claim_ref"]


def test_replaying_the_whole_set_gives_identical_trace_hashes(outcomes):
    first = [audit.trace_hash(result) for _, result in outcomes]
    second = [audit.trace_hash(result) for _, result in replay()]
    assert first == second


def test_single_claim_hash_is_stable_across_runs():
    claim = ClaimInput.model_validate(
        {
            "claim_ref": "clm-104",
            "patient_token": "pat-77",
            "facility_id": "fac-12",
            "service_code": "svc-CS-01",
            "fund": "SHIF",
            "date_of_service": "2026-10-14",
            "amount_kes": 45000,
            "member_status": "active",
        }
    ).to_claim()
    hashes = {audit.trace_hash(engine.check(claim)) for _ in range(3)}
    assert hashes == {"sha256:dc618fa5150133c49f1d80af9a7319eb90f0d53d2933f947c7ddafbe0c36e138"}


def test_dataset_has_forty_claims_covering_every_rule(outcomes):
    assert len(outcomes) == 40
    failing = {
        s["rule"].split("-")[0] for _, r in outcomes for s in r["trace"] if s["result"] != "pass"
    }
    assert {"R1", "R2", "R3", "R4", "R5", "R6", "R8"} <= failing
