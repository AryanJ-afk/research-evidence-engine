import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def evaluate_case(case, base_url):
    request = Request(
        f"{base_url.rstrip('/')}/ask",
        data=json.dumps({
            "question": case["question"],
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started_at = perf_counter()
    response_data = None
    error = None

    try:
        with urlopen(request, timeout=180) as response:
            response_data = json.load(response)
            
        if not isinstance(response_data, dict):
            raise ValueError("Expected a JSON object from /ask")

        context_ids = response_data.get("context_paper_ids")

        if (
            not isinstance(context_ids, list)
            or any(not isinstance(value, str) for value in context_ids)
        ):
            raise ValueError(
                "Missing or invalid context_paper_ids in /ask response. "
                "Check app/ask.py and rebuild the app container."
            )
            
            
        if response_data.get("status") not in {
            "answered",
            "insufficient_evidence",
        }:
            raise ValueError("Unexpected answer status")

    except HTTPError as exc:
        error = f"HTTP {exc.code}"
        exc.close()

    except (URLError, OSError, ValueError, AttributeError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    checks = {
        "status_matches_expected": False,
        "known_evidence_in_context": None,
    }

    if case["relevant_paper_ids"]:
        checks["known_evidence_in_context"] = False

    if error is None:
        checks["status_matches_expected"] = (
            response_data["status"] == case["expected_status"]
        )

        if case["relevant_paper_ids"]:
            expected = set(case["relevant_paper_ids"])
            supplied = set(response_data["context_paper_ids"])

            checks["known_evidence_in_context"] = bool(
                expected & supplied
            )

    return {
        "type": "case",
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "expected_status": case["expected_status"],
        "reference_notes": case["reference_notes"],
        "relevant_paper_ids": case["relevant_paper_ids"],
        "checks": checks,
        "error": error,
        "client_elapsed_ms": round(
            (perf_counter() - started_at) * 1000,
            2,
        ),
        "response": response_data,
        "manual_review": {
            "answers_question": None,
            "all_claims_supported": None,
            "preserves_source_scope": None,
            "notes": "",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        default="evaluation/dev_cases.jsonl",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    case_bytes = Path(args.cases).read_bytes()
    cases = [
        json.loads(line)
        for line in case_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]

    if not cases:
        parser.error("The case file is empty")

    ids = [case["id"] for case in cases]

    if len(ids) != len(set(ids)):
        parser.error("Case IDs must be unique")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "type": "metadata",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cases_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "rag_file_sha256": hashlib.sha256(
            Path("app/rag.py").read_bytes()
        ).hexdigest(),
        "base_url": args.base_url,
    }

    results = []

    with output_path.open("x", encoding="utf-8") as file:
        file.write(json.dumps(metadata) + "\n")

        for case in cases:
            result = evaluate_case(case, args.base_url)
            results.append(result)

            file.write(json.dumps(result, ensure_ascii=False) + "\n")
            file.flush()

            print(
                f"{case['id']}: "
                f"status_match="
                f"{result['checks']['status_matches_expected']}, "
                f"error={result['error']}",
                flush=True,
            )

        evidence_cases = [
            result for result in results
            if result["relevant_paper_ids"]
        ]

        summary = {
            "type": "summary",
            "cases": len(results),
            "request_errors": sum(
                result["error"] is not None
                for result in results
            ),
            "status_matches": sum(
                result["checks"]["status_matches_expected"]
                for result in results
            ),
            "known_evidence_hits": sum(
                result["checks"]["known_evidence_in_context"]
                for result in evidence_cases
            ),
            "known_evidence_cases": len(evidence_cases),
        }

        file.write(json.dumps(summary) + "\n")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()