import argparse
import csv
import statistics
import time
from itertools import cycle, islice
from pathlib import Path

from ingest.claim_schema import ClaimInput
from reasoner.parallel import check_all

SYNTHETIC_CLAIMS = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "claims.csv"


def synthetic_claims(count: int) -> list[dict]:
    with SYNTHETIC_CLAIMS.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    claims = []
    for index, row in enumerate(islice(cycle(rows), count)):
        fields = {key: value for key, value in row.items() if value}
        fields["claim_ref"] = f"bench-{index:05d}"
        fields["patient_id"] = f"{fields['patient_id']}-{index // len(rows)}"
        claims.append(ClaimInput.model_validate(fields).to_claim())
    return claims


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * fraction))]


def measure(count: int, workers: int) -> dict:
    claims = synthetic_claims(count)
    durations = []
    started = time.perf_counter()
    begin = started
    for _ in check_all(claims, [[]] * count, workers):
        now = time.perf_counter()
        durations.append(now - begin)
        begin = now
    return {
        "claims": count,
        "workers": workers,
        "total_s": time.perf_counter() - started,
        "mean_s": statistics.fmean(durations),
        "p95_s": percentile(durations, 0.95),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Time the reasoning engine on synthetic claims")
    parser.add_argument("sizes", nargs="*", type=int, default=[100, 500])
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 4])
    args = parser.parse_args()
    for size in args.sizes:
        for workers in args.workers:
            report = measure(size, workers)
            print(
                f"{report['claims']:>5} claims  {workers} worker(s)  "
                f"total {report['total_s']:6.1f}s  mean {report['mean_s'] * 1000:6.0f}ms  "
                f"p95 {report['p95_s'] * 1000:6.0f}ms"
            )


if __name__ == "__main__":
    main()
