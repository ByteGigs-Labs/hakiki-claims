import csv
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "synthetic"
SEED = 2026
REJECTION_RATE = {"PASS": 0.05, "AT_RISK": 0.45, "WILL_FAIL": 0.9}


def build() -> list[dict]:
    generator = random.Random(SEED)  # noqa: S311 - reproducible synthetic data, not security
    with (DATA / "expected.csv").open(newline="") as handle:
        expected = list(csv.DictReader(handle))
    return [
        {
            "claim_ref": row["claim_ref"],
            "outcome": "rejected"
            if generator.random() < REJECTION_RATE[row["verdict"]]
            else "accepted",
        }
        for row in expected
    ]


if __name__ == "__main__":
    with (DATA / "outcomes.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("claim_ref", "outcome"))
        writer.writeheader()
        writer.writerows(build())
