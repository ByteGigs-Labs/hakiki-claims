from ingest.claim_schema import ClaimInput

DEFAULTS = {
    "claim_ref": "clm-104",
    "patient_token": "pat-77",
    "facility_id": "fac-12",
    "service_code": "svc-OPD-01",
    "fund": "SHIF",
    "date_of_service": "2026-10-14",
    "amount_kes": 700,
    "member_status": "active",
    "icd_code": "J06.9",
    "referral_ref": "REF-1001",
    "lodging_date": "2026-10-15",
}


def make_claim(**overrides) -> dict:
    payload = {**DEFAULTS, **overrides}
    return ClaimInput.model_validate({k: v for k, v in payload.items() if v is not None}).to_claim()


def cs_claim(**overrides) -> dict:
    return make_claim(
        **{"service_code": "svc-CS-01", "amount_kes": 45000, "icd_code": "O82", **overrides}
    )


def prior(claim_ref: str, day: str, service: str = "svc-OPD-01", patient: str = "pat-77") -> dict:
    return {
        "claim_ref": claim_ref,
        "patient_token": patient,
        "service_code": service,
        "date_of_service": day,
    }


def step(result: dict, rule_id: str) -> dict:
    return next(s for s in result["trace"] if s["rule"].startswith(rule_id + "-"))
