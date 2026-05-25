"""
Run the eval dataset against the /analyze endpoint and score the responses.

Usage:
    # Start your FastAPI server first:
    fastapi dev app/main.py

    # Then in another terminal:
    python scripts/evaluate.py

Outputs:
    - Console: per-case pass/fail summary and category pass rates
    - eval_results.json: full structured results for every assertion
"""

import json
import time
from pathlib import Path
from typing import Any

import httpx


API_URL = "http://localhost:8000/analyze"
DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
RESULTS_PATH = Path(__file__).parent / "eval_results.json"
REQUEST_TIMEOUT = 90.0  # LLM calls can be slow


# ---------- Assertion checkers ----------
# Each checker takes the actual response and the expected value,
# returns (passed: bool, reason: str).

def check_should_contain_violations(actual: dict, expected: list) -> tuple[bool, str]:
    """
    Each item in `expected` can be either:
      - a string: the substring must appear in at least one violation
      - a list of strings: at least ONE of these substrings must appear (alternatives)
    Matching is case-insensitive.

    Empty `expected` list means: expect NO violations (for negative cases).
    """
    violations = actual.get("violations") or []
    violations_text = " ".join(violations).lower()

    if not expected:
        if violations:
            return False, f"expected no violations, got: {violations}"
        return True, "no violations as expected"

    missing = []
    for item in expected:
        if isinstance(item, list):
            # Any-of group: at least one alternative must match
            if not any(alt.lower() in violations_text for alt in item):
                missing.append(f"any of {item}")
        else:
            if item.lower() not in violations_text:
                missing.append(item)

    if missing:
        return False, f"missing expected {missing} in violations {violations}"
    return True, "all expected substrings found in violations"


def check_score_max(actual: dict, expected_max: float, field: str) -> tuple[bool, str]:
    """The score field must be <= expected_max (used for positive cases)."""
    scores = actual.get("scores") or {}
    score = scores.get(field)
    if score is None:
        return False, f"scores.{field} missing from response"
    if score > expected_max:
        return False, f"scores.{field}={score} exceeds max {expected_max} (false negative)"
    return True, f"scores.{field}={score} <= {expected_max}"


def check_score_min(actual: dict, expected_min: float, field: str) -> tuple[bool, str]:
    """The score field must be >= expected_min (used for negative cases)."""
    scores = actual.get("scores") or {}
    score = scores.get(field)
    if score is None:
        return False, f"scores.{field} missing from response"
    if score < expected_min:
        return False, f"scores.{field}={score} below min {expected_min} (false positive)"
    return True, f"scores.{field}={score} >= {expected_min}"


def check_should_have_citations(actual: dict, expected: bool) -> tuple[bool, str]:
    """sources list must be non-empty (RAG actually retrieved something)."""
    sources = actual.get("sources") or []
    if expected and not sources:
        return False, "expected citations but sources list is empty"
    if not expected and sources:
        return False, f"expected no citations but got {len(sources)}"
    return True, f"citations present: {len(sources)}"


def check_citation_sources_any(actual: dict, expected_any: list[str]) -> tuple[bool, str]:
    """At least one citation's doc_id must be in the expected_any list."""
    sources = actual.get("sources") or []
    cited_docs = {s.get("doc_id", "") for s in sources}
    overlap = cited_docs & set(expected_any)
    if not overlap:
        return False, (
            f"none of the citations {sorted(cited_docs)} match expected sources {expected_any}"
        )
    return True, f"matched citation source(s): {sorted(overlap)}"


# ---------- Per-case runner ----------

ASSERTION_CHECKERS = {
    "should_contain_violations": check_should_contain_violations,
    "security_score_max": lambda a, e: check_score_max(a, e, "security"),
    "maintainability_score_max": lambda a, e: check_score_max(a, e, "maintainability"),
    "readability_score_max": lambda a, e: check_score_max(a, e, "readability"),
    "security_score_min": lambda a, e: check_score_min(a, e, "security"),
    "maintainability_score_min": lambda a, e: check_score_min(a, e, "maintainability"),
    "readability_score_min": lambda a, e: check_score_min(a, e, "readability"),
    "should_have_citations": check_should_have_citations,
    "expected_citation_sources_any": check_citation_sources_any,
}


def run_case(client: httpx.Client, case: dict) -> dict:
    """Send one case to /analyze, check every assertion, return a result record."""
    # STEP 1: Submit one known code sample to the live analysis API.
    case_id = case["id"]
    print(f"\n→ {case_id} ({case['category']})")

    try:
        t0 = time.time()
        response = client.post(API_URL, json=case["input"], timeout=REQUEST_TIMEOUT)
        latency_s = time.time() - t0
        response.raise_for_status()
        actual = response.json()
    except Exception as e:
        print(f"  ✗ REQUEST FAILED: {e}")
        return {
            "id": case_id,
            "category": case["category"],
            "request_error": str(e),
            "assertions": [],
            "passed": False,
        }

    # STEP 2: Compare the analysis response with each expected outcome.
    assertion_results = []
    for assertion_name, expected_value in case["expected"].items():
        checker = ASSERTION_CHECKERS.get(assertion_name)
        if checker is None:
            assertion_results.append({
                "assertion": assertion_name,
                "passed": False,
                "reason": f"unknown assertion type: {assertion_name}",
            })
            continue

        passed, reason = checker(actual, expected_value)
        assertion_results.append({
            "assertion": assertion_name,
            "passed": passed,
            "reason": reason,
        })
        marker = "✓" if passed else "✗"
        print(f"    {marker} {assertion_name}: {reason}")

    # STEP 3: Return a traceable result record for summary reporting.
    all_passed = all(r["passed"] for r in assertion_results)
    return {
        "id": case_id,
        "category": case["category"],
        "latency_s": round(latency_s, 2),
        "actual": actual,
        "assertions": assertion_results,
        "passed": all_passed,
    }


# ---------- Summary reporting ----------

def print_summary(results: list[dict]) -> None:
    # Function logic: show outcome totals, category trends, and failure details.
    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    print("\n" + "=" * 60)
    print(f"OVERALL: {passed}/{total} cases passed ({passed / total * 100:.1f}%)")
    print("=" * 60)

    # Per-category breakdown
    by_category: dict[str, list[dict]] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)

    print("\nPer-category pass rate:")
    for category, items in sorted(by_category.items()):
        cat_passed = sum(1 for r in items if r["passed"])
        cat_total = len(items)
        print(f"  {category}: {cat_passed}/{cat_total}")

    # Per-assertion stats (which assertion types fail most often)
    assertion_stats: dict[str, dict[str, int]] = {}
    for r in results:
        for a in r["assertions"]:
            name = a["assertion"]
            stats = assertion_stats.setdefault(name, {"pass": 0, "fail": 0})
            stats["pass" if a["passed"] else "fail"] += 1

    print("\nPer-assertion pass rate:")
    for name, stats in sorted(assertion_stats.items()):
        total_a = stats["pass"] + stats["fail"]
        print(f"  {name}: {stats['pass']}/{total_a}")

    # Failures detail
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\nFAILED CASES ({len(failures)}):")
        for r in failures:
            print(f"  - {r['id']} ({r['category']})")
            if r.get("request_error"):
                print(f"      request error: {r['request_error']}")
            for a in r["assertions"]:
                if not a["passed"]:
                    print(f"      ✗ {a['assertion']}: {a['reason']}")


# ---------- Main ----------

def main() -> None:
    # STEP 1: Load the prepared evaluation examples.
    with open(DATASET_PATH) as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} test cases from {DATASET_PATH.name}")

    # STEP 2: Run each example through the API with rate-limit spacing.
    results = []
    with httpx.Client() as client:
        for i, case in enumerate(dataset):
            if i > 0:
                time.sleep(4.0)  # avoid tripping the rate limiter
            results.append(run_case(client, case))

    # STEP 3: Persist detailed evidence and print a readable scorecard.
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {RESULTS_PATH.name}")

    print_summary(results)


if __name__ == "__main__":
    main()
