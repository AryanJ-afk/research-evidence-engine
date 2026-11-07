import argparse
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def send_request(base_url, query):
    params = urlencode({"q": query, "limit": 10})
    url = f"{base_url.rstrip('/')}/search?{params}"

    result = {
        "query": query,
        "status": None,
        "error": None,
        "returned": None,
    }

    started_at = perf_counter()

    try:
        with urlopen(url, timeout=10) as response:
            body = response.read()
            result["status"] = response.status

        elapsed_ms = (perf_counter() - started_at) * 1000

        payload = json.loads(body)
        result["returned"] = payload["returned"]

    except HTTPError as error:
        elapsed_ms = (perf_counter() - started_at) * 1000
        result["status"] = error.code
        result["error"] = f"HTTP {error.code}"
        error.close()

    except (URLError, TimeoutError, OSError) as error:
        elapsed_ms = (perf_counter() - started_at) * 1000
        result["error"] = type(error).__name__

    except (ValueError, KeyError, TypeError):
        elapsed_ms = (perf_counter() - started_at) * 1000
        result["error"] = "Invalid response"

    result["latency_ms"] = round(elapsed_ms, 3)

    return result


def percentile(values, percent):
    if not values:
        return None

    ordered = sorted(values)
    index = math.ceil(len(ordered) * percent / 100) - 1
    return round(ordered[index], 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--papers", type=int, required=True)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--queries", default="benchmarks/queries.txt")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.rounds < 1 or args.papers < 1:
        parser.error("--rounds and --papers must be positive")

    output_path = Path(args.output)

    if output_path.exists():
        parser.error("Output file already exists; choose a new filename")

    query_bytes = Path(args.queries).read_bytes()
    queries = [
        line.strip()
        for line in query_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]

    if not queries:
        parser.error("The query file is empty")

    print(f"Warming up with {len(queries)} requests...")
    warmup_results = [
        send_request(args.base_url, query)
        for query in queries
    ]

    schedule = queries * args.rounds
    random.Random(42).shuffle(schedule)

    results = []

    for number, query in enumerate(schedule, start=1):
        results.append(send_request(args.base_url, query))

        if number % 10 == 0 or number == len(schedule):
            print(f"Completed {number}/{len(schedule)} requests")

    successful = [
        result["latency_ms"]
        for result in results
        if result["status"] == 200 and result["error"] is None
    ]

    failures = len(results) - len(successful)

    summary = {
        "requests": len(results),
        "successful": len(successful),
        "failed": failures,
        "error_rate_percent": round(failures / len(results) * 100, 2),
        "successful_p50_ms": percentile(successful, 50),
        "successful_p95_ms": percentile(successful, 95),
        "errors": dict(Counter(
            result["error"]
            for result in results
            if result["error"] is not None
        )),
    }

    report = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "declared_paper_count": args.papers,
        "base_url": args.base_url,
        "query_file_sha256": hashlib.sha256(query_bytes).hexdigest(),
        "rounds": args.rounds,
        "concurrency": 1,
        "result_limit": 10,
        "client_timeout_seconds": 10,
        "shuffle_seed": 42,
        "summary": summary,
        "warmup_results": warmup_results,
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"Saved report to {output_path}")


if __name__ == "__main__":
    main()