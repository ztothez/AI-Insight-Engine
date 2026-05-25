"""Post-LLM sanity checks to catch obvious hallucinated findings."""
import re


_SQL_INDICATORS = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|"
    r"execute|executemany|cursor|query)\b",
    re.IGNORECASE,
)


def filter_hallucinated_violations(violations: list[str], code_snippet: str) -> list[str]:
    """Remove violations that are likely hallucinated.
    
    Currently checks: SQL injection claims on code with no SQL indicators.
    
    Returns a filtered list. Logs nothing — caller decides what to do.
    """

    if _SQL_INDICATORS.search(code_snippet):
        return violations
    return [violation for violation in violations if "sql injection" not in violation.lower()]