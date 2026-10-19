from collections.abc import Sequence
from datetime import date

from reasoner.kb import KnowledgeBase

PREAUTH_PLACEHOLDER = "PA-PENDING"


def _target_facility(kb: KnowledgeBase, claim: dict, required_level: int) -> str | None:
    on = date.fromisoformat(claim["date_of_service"])
    return next(
        (
            facility["id"]
            for facility in kb.facilities
            if facility["level"] >= required_level and kb.contracted(facility, claim["fund"], on)
        ),
        None,
    )


def _candidate(kb: KnowledgeBase, claim: dict, result) -> tuple[dict, bool, dict] | None:
    code, *args = result.fix
    if code == "attach-preauth":
        return {"preauth_ref": PREAUTH_PLACEHOLDER}, True, {}
    if code in {"confirm-contributions", "verify-eligibility"}:
        return {"member_status": "active"}, True, {}
    if code == "reduce-amount":
        return {"amount_kes": args[0]}, False, {"cap": f"{args[0]:,}"}
    if code == "route-to-facility":
        target = _target_facility(kb, claim, args[0])
        return (
            ({"facility_id": target}, False, {"required": args[0], "target": target})
            if target
            else None
        )
    return None


def find_fixes(claim: dict, history: Sequence[dict], evaluation, kb: KnowledgeBase) -> list[dict]:
    from reasoner.engine import evaluate

    fixes = []
    for result in evaluation.results:
        if result.outcome not in {"fail", "warn"} or not result.fix:
            continue
        candidate = _candidate(kb, claim, result)
        if candidate is None:
            continue
        patch, requires_input, labels = candidate
        outcome = evaluate({**claim, **patch}, history, kb)
        repaired = next(item for item in outcome.results if item.rule == result.rule)
        if repaired.outcome != "pass":
            continue
        template = kb.rule(result.rule)["fixes"][result.fix[0]]
        fixes.append(
            {
                "action": template["en"].format_map(labels),
                "action_sw": template["sw"].format_map(labels),
                "flips_to": outcome.verdict,
                "rule": result.rule,
                "patch": patch,
                "requires_input": requires_input,
            }
        )
    return fixes
