from collections.abc import Iterable, Sequence
from datetime import date

from hyperon import E, MeTTa, S

from reasoner.kb import KnowledgeBase


def _number(metta: MeTTa, value: int | float):
    return metta.parse_single(repr(value))


def _day(iso: str) -> int:
    return date.fromisoformat(iso).toordinal()


def reference_atoms(metta: MeTTa, kb: KnowledgeBase) -> Iterable:
    for facility in kb.facilities:
        yield E(S("Facility"), S(facility["id"]), _number(metta, facility["level"]))
        for contract in facility["contracts"]:
            yield E(
                S("Contract"),
                S(facility["id"]),
                S(contract["fund"]),
                _number(metta, _day(contract["from"])),
                _number(metta, _day(contract["to"])),
            )
    for service in kb.services:
        sid = S(service["id"])
        yield E(S("Service"), sid)
        yield E(S("MinLevel"), sid, _number(metta, service["min_level"]))
        if service["requires_preauth"]:
            yield E(S("PreauthRequired"), sid)
        for fund, cap in sorted(service["tariffs"].items()):
            yield E(S("Tariff"), sid, S(fund), _number(metta, cap))
        if frequency := service.get("frequency"):
            yield E(
                S("Frequency"),
                sid,
                _number(metta, frequency["limit"]),
                _number(metta, frequency["window_days"]),
            )


def claim_atoms(metta: MeTTa, claim: dict, history: Sequence[dict]) -> Iterable:
    cid = S(claim["claim_ref"])
    yield E(S("ClaimPatient"), cid, S(claim["patient_token"]))
    yield E(S("ClaimFacility"), cid, S(claim["facility_id"]))
    yield E(S("ClaimService"), cid, S(claim["service_code"]))
    yield E(S("ClaimFund"), cid, S(claim["fund"]))
    yield E(S("ClaimDay"), cid, _number(metta, _day(claim["date_of_service"])))
    yield E(S("ClaimAmount"), cid, _number(metta, claim["amount_kes"]))
    yield E(S("MemberStatus"), cid, S(claim["member_status"]))
    if claim.get("preauth_ref"):
        yield E(S("PreauthRef"), cid, S(claim["preauth_ref"]))
    for prior in sorted(history, key=lambda item: item["claim_ref"]):
        if (
            prior["claim_ref"] == claim["claim_ref"]
            or prior["patient_token"] != claim["patient_token"]
        ):
            continue
        yield E(
            S("Prior"),
            S(prior["claim_ref"]),
            S(prior["patient_token"]),
            S(prior["service_code"]),
            _number(metta, _day(prior["date_of_service"])),
        )
