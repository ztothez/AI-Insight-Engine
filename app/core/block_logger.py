"""Audit-log writer for prompt-injection blocks.

Separated from the validator and the route so it can be:
  - Mocked in route tests
  - Reused from /agent later
  - Swapped to a different storage backend without touching routes

Design note: log_blocked_input never raises. A failure to write the audit
row must not break the user-facing rejection — the security gate is the
validator, the audit row is a diagnostic. We swallow exceptions and log
them to loguru so they're visible in stdout but don't propagate.
"""
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.input_validator import ValidationResult
from app.db.models import BlockedInput


async def log_blocked_input(
    db: AsyncSession,
    result: ValidationResult,
    input_snippet: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Insert a row into blocked_inputs documenting a rejected request.

    Args:
        db: Active async SQLAlchemy session.
        result: The ValidationResult from validate_code_input() — must be is_safe=False.
        input_snippet: The full rejected input. Stored verbatim for review.
        client_ip: Client's IP address, if available.
        user_agent: Client's User-Agent header, if available.

    Never raises. On DB failure, logs to loguru and returns silently.
    """
    if result.is_safe:
        # Defensive guard — caller should never log a safe result, but be tolerant.
        logger.warning("log_blocked_input called with is_safe=True result; ignoring")
        return

    try:
        row = BlockedInput(
            client_ip=client_ip,
            reason=result.reason.value if result.reason else "unknown",
            matched_pattern=result.matched_pattern,
            input_snippet=input_snippet,
            input_length=len(input_snippet),
            user_agent=user_agent,
        )
        db.add(row)
        await db.commit()
        logger.info(
            f"Blocked input logged: reason={row.reason} "
            f"pattern={row.matched_pattern!r} "
            f"ip={client_ip} "
            f"length={row.input_length}"
        )
    except Exception as e:
        # Audit failure must not crash the request — log it and move on.
        logger.error(f"Failed to write blocked_inputs row: {e}")
