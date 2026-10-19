import json

from scripts.export_openapi import SNAPSHOT, current_spec


def test_api_matches_the_frozen_contract():
    assert SNAPSHOT.read_text() == current_spec(), (
        "The API contract changed. If that is intended, run `python -m scripts.export_openapi`, "
        "update dashboard/src/types.ts to match, and get the pull request approved by both owners."
    )


def test_public_endpoints_are_part_of_the_contract():
    spec = json.loads(SNAPSHOT.read_text())
    public = {"/health", "/v1/auth/login", "/v1/auth/logout"}
    assert public <= set(spec["paths"])


def test_check_response_declares_the_documented_fields():
    schema = json.loads(SNAPSHOT.read_text())["components"]["schemas"]["CheckResult"]
    assert set(schema["properties"]) == {
        "claim",
        "verdict",
        "truth_value",
        "revenue_at_risk_kes",
        "trace",
        "fixes",
        "rulebook_version",
        "trace_hash",
        "prev_hash",
    }
