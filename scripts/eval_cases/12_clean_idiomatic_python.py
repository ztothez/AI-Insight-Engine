"""Short, idiomatic, well-typed function — should NOT invent violations."""

ID = "neg_clean_idiomatic_01"
CATEGORY = "negative_clean_secure_code"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''from typing import Iterable

def average(numbers: Iterable[float]) -> float:
    """Return the arithmetic mean of a sequence of numbers."""
    values = list(numbers)
    if not values:
        raise ValueError("Cannot compute average of empty sequence")
    return sum(values) / len(values)
'''
EXPECTED = {
    "should_contain_violations": [],
    "security_score_min": 8.0,
    "maintainability_score_min": 8.0,
    "readability_score_min": 8.0,
    "should_have_citations": True,
}
