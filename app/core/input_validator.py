"""
Prompt-injection and non-code input detection for the /analyze endpoint.

Design principles (deception over deterrence):
- Silent rejection: callers see a generic message, never the matched pattern.
- Log everything server-side for diagnostic and audit.
- Pure function — no FastAPI / no DB dependency — so it's trivially testable.
"""

import re
from dataclasses import dataclass
from enum import Enum


class RejectionReason(str, Enum):
    """Internal categorization of why an input was rejected.

    User never sees these — they're for server-side logs and analytics.
    """
    INSTRUCTION_OVERRIDE = "instruction_override"
    ROLE_REASSIGNMENT = "role_reassignment"
    PROMPT_LEAK_ATTEMPT = "prompt_leak_attempt"
    SYSTEM_TAG_INJECTION = "system_tag_injection"
    NON_CODE_INPUT = "non_code_input"


@dataclass(frozen=True)
class ValidationResult:
    """Result of input validation.

    Attributes:
        is_safe: True if input is acceptable, False if it should be rejected.
        reason: Internal category for logging. None when is_safe is True.
        matched_pattern: The specific pattern that matched, for diagnostics. None when safe.
    """
    is_safe: bool
    reason: RejectionReason | None = None
    matched_pattern: str | None = None


# ---------- Pattern definitions ----------
# Each tuple: (compiled regex, RejectionReason, human-readable label for logs)
# Patterns are case-insensitive. Order matters — more specific patterns first.

_INJECTION_PATTERNS: list[tuple[re.Pattern, RejectionReason, str]] = [
    # === Instruction override attempts ===
    (
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
        RejectionReason.INSTRUCTION_OVERRIDE,
        "ignore previous instructions",
    ),
    (
        re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
        RejectionReason.INSTRUCTION_OVERRIDE,
        "disregard previous instructions",
    ),
    (
        re.compile(r"forget\s+(everything|all|your|the)\s+(instructions?|previous|prior|prompts?|above|preceding)", re.IGNORECASE),
        RejectionReason.INSTRUCTION_OVERRIDE,
        "forget previous instructions",
    ),

    # === Role reassignment attempts ===
    (
        re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.IGNORECASE),
        RejectionReason.ROLE_REASSIGNMENT,
        "you are now ...",
    ),
    (
        re.compile(r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(a|an|the)\s+", re.IGNORECASE),
        RejectionReason.ROLE_REASSIGNMENT,
        "act as ...",
    ),
    (
        re.compile(r"pretend\s+(to\s+be|you\s+are)\s+", re.IGNORECASE),
        RejectionReason.ROLE_REASSIGNMENT,
        "pretend to be ...",
    ),

    # === Prompt-leak attempts ===
    (
        re.compile(
            r"(reveal|show|print|output|repeat|tell|give|expose)"
            r"(\s+(me|us))?"
            r"\s+(your|the)"
            r"\s+(original\s+|full\s+|complete\s+|system\s+)?"
            r"(prompt|instructions?|rules?|directives?)",
            re.IGNORECASE,
        ),
        RejectionReason.PROMPT_LEAK_ATTEMPT,
        "reveal system prompt",
    ),
    (
        re.compile(r"what\s+(are|were)\s+your\s+(original\s+)?(instructions?|prompts?|rules?)", re.IGNORECASE),
        RejectionReason.PROMPT_LEAK_ATTEMPT,
        "ask about original instructions",
    ),

    # === System-tag / role-tag injection ===
    # Attackers paste fake system tags hoping the model treats them as authoritative
    (
        re.compile(r"<\s*(system|assistant|user)\s*>", re.IGNORECASE),
        RejectionReason.SYSTEM_TAG_INJECTION,
        "fake role tag",
    ),
    (
        re.compile(r"###\s*(system|instruction|new\s+rules?)\s*:", re.IGNORECASE),
        RejectionReason.SYSTEM_TAG_INJECTION,
        "fake system header",
    ),
    (
        re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
        RejectionReason.SYSTEM_TAG_INJECTION,
        "chat template marker",
    ),
]


# ---------- Non-code heuristic ----------
# Code has identifying features: keywords, operators, indentation, parens.
# Pure-prose inputs lack these. This is a soft heuristic — not bulletproof.

_CODE_INDICATORS = re.compile(
    r"\b(def|class|import|from|return|if|elif|else|for|while|try|except|"
    r"function|const|let|var|public|private|static|void|int|string|"
    r"SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b|"
    r"[(){};=]|"
    r"^\s{2,}\S",
    re.IGNORECASE | re.MULTILINE,
)

_MIN_CODE_LENGTH = 10  # below this, anything goes — too short to judge


def _looks_like_code(text: str) -> bool:
    """Soft heuristic: does this text contain code-like features?

    Returns True if the text either is too short to judge, or contains
    at least 2 code indicators. False otherwise.
    """
    # Function logic: accept short input or require multiple code signals.
    if len(text.strip()) < _MIN_CODE_LENGTH:
        return True  # too short to reject — let it through

    matches = _CODE_INDICATORS.findall(text)
    return len(matches) >= 2


# ---------- Public API ----------

def validate_code_input(code_snippet: str) -> ValidationResult:
    """Validate a code snippet before sending it to the LLM.

    Returns ValidationResult(is_safe=True) if the input looks like legitimate code.
    Returns ValidationResult(is_safe=False, reason=..., matched_pattern=...) otherwise.

    The reason and matched_pattern are for SERVER-SIDE LOGGING ONLY.
    Callers must NOT echo these back to the user.
    """
    # STEP 1: Reject empty submissions as unusable analysis input.
    if not code_snippet or not code_snippet.strip():
        return ValidationResult(
            is_safe=False,
            reason=RejectionReason.NON_CODE_INPUT,
            matched_pattern="empty input",
        )

    # STEP 2: Block known prompt-manipulation patterns before LLM processing.
    for pattern, reason, label in _INJECTION_PATTERNS:
        if pattern.search(code_snippet):
            return ValidationResult(
                is_safe=False,
                reason=reason,
                matched_pattern=label,
            )

    # STEP 3: Reject prose-like input that lacks enough code indicators.
    if not _looks_like_code(code_snippet):
        return ValidationResult(
            is_safe=False,
            reason=RejectionReason.NON_CODE_INPUT,
            matched_pattern="no code indicators detected",
        )

    # STEP 4: Approve code-like input that passed all security checks.
    return ValidationResult(is_safe=True)
