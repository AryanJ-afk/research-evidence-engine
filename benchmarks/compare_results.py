import json
from pathlib import Path
from statistics import median


RESULTS_DIR = Path("benchmarks/results")


def summarize(label):
    reports = [
        json.loads(
            (RESULTS_DIR / f"{label}-run{run}.json").read_text()
        )
        for run in (1, 2, 3)
    ]

    p95_values = [
        report["summary"]["successful_p95_ms"]
        for report in reports
    ]

    if any(value is None for value in p95_values):
        raise ValueError(f"{label}: a run has no successful requests")

    failures = sum(
        report["summary"]["failed"] for report in reports
    )

    print(f"{label}")
    print(f"  Per-run p95: {p95_values}")
    print(f"  Median p95: {median(p95_values):.2f} ms")
    print(f"  Total failures: {failures}")

    return median(p95_values), failures


before, before_failures = summarize("keyword-unindexed-10k")
after, after_failures = summarize("keyword-indexed-10k")

if before_failures or after_failures:
    print("Failures occurred; successful-request latency alone is insufficient.")
else:
    reduction = (before - after) / before * 100
    print(f"\nReduction in median per-run p95: {reduction:.2f}%")