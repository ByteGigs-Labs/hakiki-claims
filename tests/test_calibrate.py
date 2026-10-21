import json
import subprocess
import sys
from pathlib import Path

import pytest

from reasoner import calibrate
from scripts.build_outcomes import build

SYNTHETIC = Path(__file__).resolve().parents[1] / "data" / "synthetic"
HEADER = (
    "claim_ref,patient_id,facility_id,service_code,fund,date_of_service,amount_kes,"
    "member_status,icd_code,referral_ref,lodging_date\n"
)
CLAIMS = (
    HEADER
    + "clm-a,PT-001,fac-12,svc-CS-01,SHIF,2026-10-14,45000,active,O82,REF-1,2026-10-15\n"
    + "clm-b,PT-002,fac-12,svc-CS-01,SHIF,2026-10-14,45000,active,O82,REF-2,2026-10-15\n"
    + "clm-c,PT-003,fac-12,svc-OPD-01,SHIF,2026-10-14,700,active,J06.9,REF-3,2026-10-15\n"
)
OUTCOMES = "claim_ref,outcome\nclm-a,rejected\nclm-b,accepted\nclm-c,accepted\n"


@pytest.fixture
def files(tmp_path):
    (tmp_path / "claims.csv").write_text(CLAIMS)
    (tmp_path / "outcomes.csv").write_text(OUTCOMES)
    return tmp_path


def test_smoothing_blends_the_prior_with_what_was_observed():
    assert calibrate.smoothed_strength(1, 2, 0.95) == pytest.approx((1 + 5 * 0.95) / 7)
    assert calibrate.smoothed_strength(0, 0, 0.6) == pytest.approx(0.6)
    assert calibrate.smoothed_strength(100, 100, 0.2) == pytest.approx(101 / 105)


def test_confidence_grows_with_evidence_and_never_reaches_certainty():
    values = [calibrate.evidence_confidence(n) for n in (0, 1, 5, 50, 5000)]
    assert values == sorted(values) and values[0] == 0
    assert values[2] == pytest.approx(0.5) and values[-1] == calibrate.MAX_CONFIDENCE


def test_a_hand_made_example_gives_the_expected_precision(files):
    reports = {
        item.rule: item
        for item in calibrate.calibrate(
            calibrate.read_claims(files / "claims.csv"),
            calibrate.read_outcomes(files / "outcomes.csv"),
        )
    }
    preauth = reports["R3"]
    assert (preauth.fired, preauth.rejected_when_fired, preauth.precision) == (2, 1, 0.5)
    assert preauth.current_strength == 0.95
    assert preauth.suggested_strength == round((1 + 5 * 0.95) / 7, 4)
    assert preauth.suggested_confidence == round(2 / 7, 4)
    assert reports["R1"].fired == 0 and reports["R1"].suggested_strength is None


def test_claims_without_outcomes_are_ignored(files):
    outcomes = calibrate.read_outcomes(files / "outcomes.csv")
    only_a = {"clm-a": outcomes["clm-a"]}
    reports = calibrate.calibrate(calibrate.read_claims(files / "claims.csv"), only_a)
    assert next(item for item in reports if item.rule == "R3").fired == 1


def test_the_command_line_prints_a_table_and_writes_a_report(files):
    report = files / "report.json"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "reasoner.calibrate",
            "--claims",
            str(files / "claims.csv"),
            "--outcomes",
            str(files / "outcomes.csv"),
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "R3" in done.stdout and "3 claims with outcomes, 1 rejected" in done.stdout
    data = json.loads(report.read_text())
    assert data["claims"] == 3 and len(data["rules"]) == 11 and data["rulebook_version"]


@pytest.mark.parametrize(
    "outcomes", ["claim_ref,outcome\nclm-a,maybe\n", "claim_ref,outcome\nzzz,rejected\n"]
)
def test_bad_outcome_files_fail_with_a_clear_message(files, outcomes):
    (files / "outcomes.csv").write_text(outcomes)
    with pytest.raises(calibrate.CalibrationError):
        calibrate.run(files / "claims.csv", files / "outcomes.csv", None)


def test_the_synthetic_outcomes_are_reproducible():
    stored = (SYNTHETIC / "outcomes.csv").read_text().splitlines()[1:]
    assert stored == [f"{row['claim_ref']},{row['outcome']}" for row in build()]


def test_the_synthetic_report_is_deterministic(tmp_path):
    first = calibrate.run(SYNTHETIC / "claims.csv", SYNTHETIC / "outcomes.csv", tmp_path / "a.json")
    assert "R3" in first and "21 rejected" in first
    report = json.loads((tmp_path / "a.json").read_text())
    assert all(0 <= item["precision"] <= 1 for item in report["rules"] if item["fired"])
