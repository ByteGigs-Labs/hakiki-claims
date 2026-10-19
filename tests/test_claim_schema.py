import pytest
from pydantic import ValidationError

from ingest.claim_schema import ClaimInput
from ingest.pseudonymise import patient_token

VALID = {
    "patient_token": "pat-77",
    "facility_id": "fac-12",
    "service_code": "svc-CS-01",
    "fund": "SHIF",
    "date_of_service": "2026-10-14",
    "amount_kes": 45000,
}


def parse(**overrides) -> ClaimInput:
    return ClaimInput.model_validate({**VALID, **overrides})


def test_valid_claim_normalises_to_engine_input():
    claim = parse().to_claim()
    assert claim["amount_kes"] == 45000 and claim["member_status"] == "unknown"
    assert claim["claim_ref"].startswith("clm-")


def test_derived_claim_reference_is_stable_and_ignores_amount():
    assert parse().to_claim()["claim_ref"] == parse(amount_kes=1).to_claim()["claim_ref"]


def test_explicit_claim_reference_is_kept():
    assert parse(claim_ref="clm-104").to_claim()["claim_ref"] == "clm-104"


def test_patient_id_is_replaced_by_a_token_and_never_kept():
    claim = ClaimInput.model_validate(
        {**{k: v for k, v in VALID.items() if k != "patient_token"}, "patient_id": "A123456"}
    )
    assert claim.patient_id is None
    assert claim.patient_token == patient_token("A123456")
    assert "A123456" not in claim.model_dump_json()


@pytest.mark.parametrize("extra", [{"patient_id": "A123456"}, {"patient_token": None}])
def test_exactly_one_patient_identifier_is_required(extra):
    with pytest.raises(ValidationError):
        parse(**extra)


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount_kes": 0},
        {"amount_kes": -5},
        {"amount_kes": 10_000_001},
        {"amount_kes": 10.123},
        {"fund": "NHIF"},
        {"date_of_service": "2024-09-30"},
        {"date_of_service": "2999-01-01"},
        {"service_code": "svc CS 01"},
        {"service_code": "x" * 51},
        {"facility_id": "fac-12) (Result"},
        {"preauth_ref": "no spaces allowed"},
        {"icd_code": "not-an-icd"},
        {"member_status": "maybe"},
        {"unexpected_field": "x"},
    ],
)
def test_invalid_claims_are_rejected(overrides):
    with pytest.raises(ValidationError):
        parse(**overrides)


def test_blank_optional_fields_count_as_missing():
    claim = parse(preauth_ref="  ", icd_code="").to_claim()
    assert claim["preauth_ref"] is None and claim["icd_code"] is None
