from datetime import date

from hyperon import MeTTa

from reasoner.facts import icd_category
from reasoner.kb import KnowledgeBase

MAX_SHOWN = 5
ABSENT, OPTIONAL = "!", "?"


def _bindings(claim: dict, detail: dict) -> dict:
    category = icd_category(claim["icd_code"]) if claim.get("icd_code") else ""
    return {
        **detail,
        "c": claim["claim_ref"],
        "service": claim["service_code"],
        "fund": claim["fund"],
        "facility": claim["facility_id"],
        "patient": claim["patient_token"],
        "category": category,
        "day": date.fromisoformat(claim["date_of_service"]).toordinal(),
    }


def _matches(metta: MeTTa, pattern: str) -> list[str]:
    (found,) = metta.run(f"!(match &self {pattern} {pattern})")
    return sorted(str(atom) for atom in found)


def premises_for(
    metta: MeTTa, kb: KnowledgeBase, claim: dict, rule: str, outcome: str, reason: str, detail: dict
) -> list[str]:
    templates = kb.premises[f"{rule}.{outcome}.{reason}"]
    bindings = _bindings(claim, detail)
    shown = []
    for template in templates:
        marker = template[0] if template[0] in (ABSENT, OPTIONAL) else ""
        pattern = template[len(marker) :].format_map(bindings)
        found = _matches(metta, pattern)
        if marker == ABSENT:
            if found:
                raise RuntimeError(f"{rule} {reason}: expected {pattern} to be absent")
            shown.append(f"(not {pattern})")
            continue
        if not found and not marker:
            raise RuntimeError(f"{rule} {reason}: premise {pattern} is not in the knowledge base")
        shown.extend(found[:MAX_SHOWN])
    return shown
