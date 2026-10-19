import re

RULE_ID = re.compile(r"\bR\d{1,2}\b")
LARGE_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
LARGE_THRESHOLD = 100
MAX_LENGTH = 1500


def _numbers(text: str) -> set[float]:
    return {float(token.replace(",", "")) for token in LARGE_NUMBER.findall(RULE_ID.sub("", text))}


def _known_numbers(result: dict) -> set[float]:
    sources = [str(result["revenue_at_risk_kes"])]
    for step in result["trace"]:
        sources += [str(value) for value in step["values"].values()]
    sources += [fix["action"] for fix in result["fixes"]]
    return {number for source in sources for number in _numbers(source)}


def narration_matches_trace(text: str, claimed_verdict: str, result: dict) -> bool:
    if claimed_verdict != result["verdict"] or not text.strip() or len(text) > MAX_LENGTH:
        return False
    known_rules = {step["rule"].split("-")[0] for step in result["trace"]}
    failing_rules = {
        step["rule"].split("-")[0] for step in result["trace"] if step["result"] in {"fail", "warn"}
    }
    mentioned = set(RULE_ID.findall(text))
    if not failing_rules <= mentioned or not mentioned <= known_rules:
        return False
    known = _known_numbers(result)
    return all(number < LARGE_THRESHOLD or number in known for number in _numbers(text))
