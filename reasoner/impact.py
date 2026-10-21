import argparse
import csv
import hashlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ingest.claim_schema import ClaimInput
from reasoner import engine
from reasoner.kb import KB_DIR, KnowledgeBase, load_kb

REPO = KB_DIR.parent
SYNTHETIC_CLAIMS = REPO / "data" / "synthetic" / "claims.csv"
BEHAVIOUR = (
    "rules/*.metta",
    "combine.metta",
    "citations.json",
    "premises.json",
    "reference/*.json",
)


@dataclass(frozen=True)
class Outcome:
    verdict: str
    strength: float
    rules: tuple[str, ...]


@dataclass(frozen=True)
class Change:
    claim_ref: str
    before: Outcome
    after: Outcome


def behaviour_fingerprint(directory: Path) -> str:
    digest = hashlib.sha256()
    for pattern in BEHAVIOUR:
        for path in sorted(directory.glob(pattern)):
            digest.update(path.relative_to(directory).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def version_is_stale(base: Path, current: Path) -> bool:
    changed = behaviour_fingerprint(base) != behaviour_fingerprint(current)
    return changed and (base / "VERSION").read_text() == (current / "VERSION").read_text()


def read_claims(path: Path = SYNTHETIC_CLAIMS) -> list[dict]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ClaimInput.model_validate({key: value for key, value in row.items() if value}).to_claim()
        for row in rows
    ]


def outcomes(claims: list[dict], kb: KnowledgeBase) -> dict[str, Outcome]:
    history: list[dict] = []
    found = {}
    for claim in claims:
        evaluation = engine.evaluate(claim, history, kb)
        found[claim["claim_ref"]] = Outcome(
            evaluation.verdict,
            evaluation.strength,
            tuple(r.rule for r in evaluation.results if r.outcome in {"fail", "warn"}),
        )
        history.append(claim)
    return found


def compare(claims: list[dict], before: KnowledgeBase, after: KnowledgeBase) -> list[Change]:
    old, new = outcomes(claims, before), outcomes(claims, after)
    return [Change(ref, old[ref], new[ref]) for ref in old if old[ref] != new[ref]]


def render(changes: list[Change], total: int, before: KnowledgeBase, after: KnowledgeBase) -> str:
    moved = sum(change.before.verdict != change.after.verdict for change in changes)
    lines = [
        f"### Rulebook impact: {before.version} → {after.version}",
        "",
        f"{total} synthetic claims replayed. {moved} changed verdict, "
        f"{len(changes) - moved} changed only in strength or firing rules.",
    ]
    if changes:
        lines += ["", "| Claim | Verdict | Strength | Rules firing |", "|---|---|---|---|"]
        for change in changes:
            fired = [", ".join(side.rules) or "-" for side in (change.before, change.after)]
            lines.append(
                f"| {change.claim_ref} | {change.before.verdict} → {change.after.verdict} "
                f"| {change.before.strength} → {change.after.strength} | {fired[0]} → {fired[1]} |"
            )
    return "\n".join(lines)


def extract_kb(ref: str, destination: Path) -> Path:
    archive = subprocess.run(
        ["git", "archive", ref, "kb"], cwd=REPO, capture_output=True, check=True
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(destination)], input=archive, check=True)
    return destination / "kb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Show how a rulebook change moves verdicts")
    parser.add_argument("--base", required=True, help="git ref holding the previous rulebook")
    parser.add_argument("--check-version", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as scratch:
        base_dir = extract_kb(args.base, Path(scratch))
        before, after = load_kb(base_dir), load_kb(KB_DIR)
        claims = read_claims()
        print(render(compare(claims, before, after), len(claims), before, after))
        if args.check_version and version_is_stale(base_dir, KB_DIR):
            sys.exit("The rulebook changed but kb/VERSION was not bumped")


if __name__ == "__main__":
    main()
