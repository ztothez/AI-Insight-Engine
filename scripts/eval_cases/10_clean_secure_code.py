"""Idiomatic, secure Python — should NOT be flagged. False-positive guard."""

ID = "neg_clean_secure_01"
CATEGORY = "negative_clean_secure_code"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """Return the API key from environment, raising if missing."""
    key = os.environ.get("API_KEY")
    if not key:
        raise RuntimeError("API_KEY environment variable is not set")
    return key

def safe_divide(numerator: float, denominator: float) -> float | None:
    """Divide two numbers, returning None on division by zero."""
    if denominator == 0:
        logger.warning("Attempted division by zero")
        return None
    return numerator / denominator
'''
EXPECTED = {
    "should_contain_violations": [],
    "security_score_min": 7.0,
    "maintainability_score_min": 7.0,
    "should_have_citations": True,
}
