from statistics import median, quantiles
from time import perf_counter
from typing import Any
import json
from datetime import datetime, timezone
from pathlib import Path
from search import keyword_search

def benchmark_keyword_search(query: str, runs: int=20, limit: int=5) -> dict[str, Any]:
    if runs < 2:
        raise ValueError("Runs must be at least 2")
    
    keyword_search(query, limit)
    
    latencies_ms = []
    
    for i in range(runs):
        start = perf_counter()
        results = keyword_search(query, limit)
        elapsed_ms = (perf_counter() - start) * 1000
        latencies_ms.append(elapsed_ms)
        
    return {
        "query": query,
        "runs": runs,
        "limit": limit,
        "warmup_runs": 1,
        "result_count": len(results),
        "median_ms": median(latencies_ms),
        "p95_ms": quantiles(
            latencies_ms, n=100, method="inclusive"
        )[94],
        "latencies_ms": latencies_ms,
    }
    
def run_benchmark_suite(query_file: Path, output_file: Path) -> None:
    queries = json.loads(query_file.read_text(encoding="utf-8"))

    results = []
    for query in queries:
        result = benchmark_keyword_search(query)
        results.append(result)

    report = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "method": "Sequential keyword searches, each with a new database connection",
        "cache_conditions": "One untimed warmup per query; caches not reset",
        "results": results,
    }

    output_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )