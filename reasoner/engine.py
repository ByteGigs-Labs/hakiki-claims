import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from string import Formatter

from hyperon import ExpressionAtom, GroundedAtom, MeTTa, SymbolAtom

from reasoner import audit
from reasoner.facts import claim_atoms, reference_atoms
from reasoner.kb import IMPLEMENTED_RULES, KnowledgeBase, load_kb

VERDICT_RANK = {"PASS": 0, "AT_RISK": 1, "WILL_FAIL": 2}
SCORE_PRECISION = 4


@dataclass(frozen=True)
class RuleResult:
    rule: str
    outcome: str
    strength: float
    confidence: float
    reason: str
    detail: dict
    fix: tuple | None


@dataclass(frozen=True)
class Evaluation:
    results: tuple[RuleResult, ...]
    verdict: str
    strength: float
    confidence: float


def to_python(atom):
    if isinstance(atom, ExpressionAtom):
        return [to_python(child) for child in atom.get_children()]
    if isinstance(atom, SymbolAtom):
        return atom.get_name()
    if isinstance(atom, GroundedAtom):
        return atom.get_object().content
    raise TypeError(f"unsupported atom {atom!r}")


def _round(value: float) -> float:
    return round(float(value), SCORE_PRECISION)


def _parse_result(raw: list) -> RuleResult:
    _, rule, outcome, (_, strength, confidence), (_, *entries) = raw
    detail = {entry[0]: entry[1] if len(entry) == 2 else entry[1:] for entry in entries}
    fix = detail.pop("fix", None)
    return RuleResult(
        rule=rule,
        outcome=outcome,
        strength=_round(strength),
        confidence=_round(confidence),
        reason=detail.pop("reason"),
        detail=detail,
        fix=tuple(fix) if isinstance(fix, list) else ((fix,) if fix else None),
    )


CLAIM_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _run(metta: MeTTa, expression: str):
    (results,) = metta.run(f"!{expression}")
    if len(results) != 1:
        raise RuntimeError(f"expected exactly one result from {expression}, got {len(results)}")
    return results[0]


def evaluate(
    claim: dict, history: Sequence[dict] = (), kb: KnowledgeBase | None = None
) -> Evaluation:
    kb = kb or load_kb()
    if not CLAIM_REFERENCE.match(claim["claim_ref"]):
        raise ValueError("claim_ref contains characters that are not allowed")
    metta = MeTTa()
    metta.run(kb.program)
    space = metta.space()
    for atom in (*reference_atoms(metta, kb), *claim_atoms(metta, claim, history)):
        space.add_atom(atom)
    raw_results = [
        _run(metta, f"(check-{rule.lower()} {claim['claim_ref']})") for rule in IMPLEMENTED_RULES
    ]
    cons = "Nil"
    for result in reversed(raw_results):
        cons = f"(Cons {result} {cons})"
    _, name, (_, strength, confidence) = to_python(_run(metta, f"(combine {cons})"))
    return Evaluation(
        results=tuple(_parse_result(to_python(atom)) for atom in raw_results),
        verdict=name,
        strength=_round(strength),
        confidence=_round(confidence),
    )


def _plain(value: int | float) -> int | float:
    return int(value) if float(value) == int(value) else value


def _context(claim: dict, result: RuleResult) -> dict:
    values = {
        "date": claim["date_of_service"],
        "facility": claim["facility_id"],
        "service": claim["service_code"],
        "fund": claim["fund"],
        "amount": claim["amount_kes"],
        **result.detail,
    }
    return {
        key: f"{_plain(value):,}"
        if isinstance(value, int | float) and key in {"amount", "cap"}
        else value
        for key, value in values.items()
    }


def _message(kb: KnowledgeBase, result: RuleResult, language: str) -> str:
    return kb.rule(result.rule)["messages"][f"{result.outcome}.{result.reason}"][language]


def _used_values(kb: KnowledgeBase, claim: dict, result: RuleResult) -> dict:
    fields = {
        name
        for language in ("en", "sw")
        for _, name, _, _ in Formatter().parse(_message(kb, result, language))
        if name
    }
    context = _context(claim, result)
    return {name: context[name] for name in sorted(fields)}


def render_fact(kb: KnowledgeBase, claim: dict, result: RuleResult) -> str:
    return _message(kb, result, "en").format_map(_context(claim, result))


def revenue_at_risk(claim: dict, evaluation: Evaluation) -> int | float:
    if evaluation.verdict == "WILL_FAIL":
        return claim["amount_kes"]
    if evaluation.verdict == "AT_RISK":
        return _plain(round(claim["amount_kes"] * evaluation.strength, 2))
    return 0


def build_trace(kb: KnowledgeBase, claim: dict, evaluation: Evaluation) -> list[dict]:
    steps = []
    for index, result in enumerate(evaluation.results, start=1):
        step = {
            "step": index,
            "rule": kb.rule_label(result.rule),
            "result": result.outcome,
            "fact": render_fact(kb, claim, result),
            "citation": f"kb/citations.json#{result.rule}",
            "reason": result.reason,
            "values": _used_values(kb, claim, result),
        }
        if result.outcome != "skip":
            step["stv"] = [result.strength, result.confidence]
        steps.append(step)
    return steps


def check(claim: dict, history: Sequence[dict] = (), kb: KnowledgeBase | None = None) -> dict:
    from reasoner.fixes import find_fixes

    kb = kb or load_kb()
    evaluation = evaluate(claim, history, kb)
    return {
        "claim": claim["claim_ref"],
        "verdict": evaluation.verdict,
        "truth_value": {"strength": evaluation.strength, "confidence": evaluation.confidence},
        "revenue_at_risk_kes": revenue_at_risk(claim, evaluation),
        "trace": build_trace(kb, claim, evaluation),
        "fixes": find_fixes(claim, history, evaluation, kb),
        "rulebook_version": kb.version,
    }


def main() -> None:
    from ingest.claim_schema import ClaimInput

    parser = argparse.ArgumentParser(description="Check one claim against the SHA rulebook")
    parser.add_argument("--claim", required=True, help="path to a claim JSON file")
    with open(parser.parse_args().claim) as handle:
        claim = ClaimInput.model_validate(json.load(handle)).to_claim()
    result = check(claim)
    result["trace_hash"] = audit.trace_hash(result)
    result["prev_hash"] = audit.GENESIS_HASH
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
