import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from ingest.csv_import import parse_csv
from reasoner import engine
from reasoner.kb import load_kb

PRIOR_WEIGHT = 5
EVIDENCE_HORIZON = 5
MAX_CONFIDENCE = 0.95
MAX_ROWS = 100_000
RISK_OUTCOMES = {"fail", "warn"}
OUTCOMES = {"accepted", "rejected"}


class CalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class RuleReport:
    rule: str
    name: str
    fired: int
    rejected_when_fired: int
    missed_rejections: int
    precision: float | None
    current_strength: float | None
    suggested_strength: float | None
    suggested_confidence: float | None


def read_outcomes(path: Path) -> dict[str, bool]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    outcomes = {}
    for row in rows:
        value = (row.get("outcome") or "").strip().lower()
        if value not in OUTCOMES or not (row.get("claim_ref") or "").strip():
            raise CalibrationError("Outcomes need claim_ref and outcome (accepted or rejected)")
        outcomes[row["claim_ref"].strip()] = value == "rejected"
    return outcomes


def read_claims(path: Path) -> list[dict]:
    parsed = parse_csv(path.read_bytes(), MAX_ROWS)
    if parsed.errors:
        raise CalibrationError(f"{len(parsed.errors)} claim rows are invalid")
    return [item["claim"] for item in parsed.claims]


def smoothed_strength(rejected: int, fired: int, prior: float) -> float:
    return (rejected + PRIOR_WEIGHT * prior) / (fired + PRIOR_WEIGHT)


def evidence_confidence(fired: int) -> float:
    return min(MAX_CONFIDENCE, fired / (fired + EVIDENCE_HORIZON))


def rule_ids() -> list[str]:
    return sorted(load_kb().citations["rules"], key=lambda rule_id: int(rule_id[1:]))


def observe(claims: list[dict], rejected: dict[str, bool]) -> dict[str, dict]:
    history: list[dict] = []
    seen = defaultdict(lambda: {"fired": 0, "hit": 0, "strengths": [], "missed": 0})
    rules = rule_ids()
    for claim in claims:
        verdict = engine.evaluate(claim, history).results
        history.append(
            {
                key: claim[key]
                for key in ("claim_ref", "patient_token", "service_code", "date_of_service")
            }
        )
        if claim["claim_ref"] not in rejected:
            continue
        was_rejected = rejected[claim["claim_ref"]]
        fired = {result.rule: result for result in verdict if result.outcome in RISK_OUTCOMES}
        for rule in rules:
            entry = seen[rule]
            if rule in fired:
                entry["fired"] += 1
                entry["hit"] += was_rejected
                entry["strengths"].append(fired[rule].strength)
            elif was_rejected:
                entry["missed"] += 1
    return seen


def calibrate(claims: list[dict], outcomes: dict[str, bool]) -> list[RuleReport]:
    seen = observe(claims, outcomes)
    kb = load_kb()
    reports = []
    for rule_id in rule_ids():
        entry = seen[rule_id]
        fired, strengths = entry["fired"], entry["strengths"]
        current = sum(strengths) / len(strengths) if strengths else None
        reports.append(
            RuleReport(
                rule=rule_id,
                name=kb.rule(rule_id)["name"],
                fired=fired,
                rejected_when_fired=entry["hit"],
                missed_rejections=entry["missed"],
                precision=round(entry["hit"] / fired, 4) if fired else None,
                current_strength=round(current, 4) if fired else None,
                suggested_strength=(
                    round(smoothed_strength(entry["hit"], fired, current), 4) if fired else None
                ),
                suggested_confidence=round(evidence_confidence(fired), 4) if fired else None,
            )
        )
    return reports


def render_table(reports: list[RuleReport], claims: int, rejections: int) -> str:
    def cell(value: float | None) -> str:
        return "-" if value is None else f"{value:.2f}"

    lines = [
        f"{claims} claims with outcomes, {rejections} rejected",
        f"{'rule':<5}{'name':<22}{'fired':>6}{'rejected':>9}{'missed':>7}"
        f"{'precision':>10}{'current':>9}{'suggest':>9}{'conf':>6}",
    ]
    for item in reports:
        lines.append(
            f"{item.rule:<5}{item.name[:21]:<22}{item.fired:>6}{item.rejected_when_fired:>9}"
            f"{item.missed_rejections:>7}{cell(item.precision):>10}"
            f"{cell(item.current_strength):>9}{cell(item.suggested_strength):>9}"
            f"{cell(item.suggested_confidence):>6}"
        )
    return "\n".join(lines)


def run(claims_path: Path, outcomes_path: Path, report_path: Path | None) -> str:
    outcomes = read_outcomes(outcomes_path)
    claims = read_claims(claims_path)
    matched = {claim["claim_ref"] for claim in claims} & outcomes.keys()
    if not matched:
        raise CalibrationError("No claim_ref appears in both files")
    reports = calibrate(claims, outcomes)
    rejections = sum(outcomes[ref] for ref in matched)
    if report_path:
        report_path.write_text(
            json.dumps(
                {
                    "claims": len(matched),
                    "rejected": rejections,
                    "rulebook_version": load_kb().version,
                    "rules": [asdict(item) for item in reports],
                },
                indent=2,
            )
            + "\n"
        )
    return render_table(reports, len(matched), rejections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare rule verdicts with real claim outcomes")
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("calibration-report.json"))
    args = parser.parse_args()
    try:
        print(run(args.claims, args.outcomes, args.report))
    except CalibrationError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
