"""Classify an incoming /audit request to decide which backend to call."""
from enum import Enum
import re


class RouteTarget(str, Enum):
    RAG = "rag"
    AGENT = "agent"


_QUESTION_INDICATORS = re.compile(
    r"\b(what|how|why|should|when|where|which|can\s+you|explain)\b",
    re.IGNORECASE,
)

_CODE_INDICATORS = re.compile(
    r"\b(def|class|import|from|return|SELECT|INSERT|function|const|let|var)\b|"
    r"[(){};]",
    re.IGNORECASE,
)


def route(code_snippet: str) -> RouteTarget:
    """Decide whether to send to RAG (/analyze) or agent (/agent)."""
    stripped = code_snippet.strip()
    
    # Strong question signal: question word at the very start
    first_chunk = stripped[:30].lower()
    if _QUESTION_INDICATORS.match(first_chunk):
        return RouteTarget.AGENT
    
    # Now check the body
    question_match = _QUESTION_INDICATORS.search(stripped)
    code_matches = _CODE_INDICATORS.findall(stripped)
    
    # Strong code signal → RAG, regardless of question words inside
    if len(code_matches) >= 3:
        return RouteTarget.RAG
    
    # Question word + no code → agent
    if question_match and not code_matches:
        return RouteTarget.AGENT
    
    # Short with question word + light code → agent
    if question_match and len(stripped) < 200:
        return RouteTarget.AGENT
    
    return RouteTarget.RAG