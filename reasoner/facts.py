from collections.abc import Iterable, Sequence
from datetime import date

from hyperon import E, MeTTa, S

from reasoner.kb import KnowledgeBase


def _number(metta: MeTTa, value: int | float):
    return metta.parse_single(repr(value))


def _day(iso: str) -> int:
    return date.fromisoformat(iso).toordinal()


def expand_icd_range(span: str) -> list[str]:
    start, end = (part.strip() for part in span.split("-"))
    first, last = (start[0], int(start[1:])), (end[0], int(end[1:]))
    categories = []
    for letter in range(ord(first[0]), ord(last[0]) + 1):
        low = first[1] if letter == ord(first[0]) else 0
        high = last[1] if letter == ord(last[0]) else 99
        categories += [f"{chr(letter)}{number:02d}" for number in range(low, high + 1)]
    return categories


def icd_category(code: str) -> str:
    return code[:3].upper()


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
    for fund in kb.referral_funds:
        yield E(S("ReferralFund"), S(fund))
    for service in kb.services:
        sid = S(service["id"])
        yield E(S("Service"), sid)
        if service["emergency_service"]:
            yield E(S("EmergencyService"), sid)
        for fund, level in sorted(service["levels"].items()):
            yield E(S("MinLevel"), sid, S(fund), _number(metta, level))
        for fund in service["preauth_funds"]:
            yield E(S("PreauthRequired"), sid, S(fund))
        for fund, cap in sorted(service["tariffs"].items()):
            yield E(S("Tariff"), sid, S(fund), _number(metta, cap))
        for fund in service.get("verified_tariffs", []):
            yield E(S("TariffVerified"), sid, S(fund))
        if frequency := service.get("frequency"):
            yield E(
                S("Frequency"),
                sid,
                _number(metta, frequency["limit"]),
                _number(metta, frequency["window_days"]),
            )
        if service["icd_categories"]:
            yield E(S("IcdRestricted"), sid)
            for span in service["icd_categories"]:
                for category in expand_icd_range(span):
                    yield E(S("IcdOk"), sid, S(category))


def claim_atoms(metta: MeTTa, claim: dict, history: Sequence[dict]) -> Iterable:
    cid = S(claim["claim_ref"])
    yield E(S("ClaimPatient"), cid, S(claim["patient_token"]))
    yield E(S("ClaimFacility"), cid, S(claim["facility_id"]))
    yield E(S("ClaimService"), cid, S(claim["service_code"]))
    yield E(S("ClaimFund"), cid, S(claim["fund"]))
    yield E(S("ClaimDay"), cid, _number(metta, _day(claim["date_of_service"])))
    yield E(S("ClaimAmount"), cid, _number(metta, claim["amount_kes"]))
    yield E(S("MemberStatus"), cid, S(claim["member_status"]))
    discharge = claim.get("discharge_date") or claim["date_of_service"]
    yield E(S("LodgingDelay"), cid, _number(metta, _day(claim["lodging_date"]) - _day(discharge)))
    if claim.get("emergency"):
        yield E(S("Emergency"), cid)
    if claim.get("preauth_ref"):
        yield E(S("PreauthRef"), cid, S(claim["preauth_ref"]))
    if claim.get("referral_ref"):
        yield E(S("ReferralRef"), cid, S(claim["referral_ref"]))
    if claim.get("icd_code"):
        yield E(S("IcdCode"), cid, S(claim["icd_code"]))
        yield E(S("IcdCategory"), cid, S(icd_category(claim["icd_code"])))
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
