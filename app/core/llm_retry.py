"""Retry wrapper for LLM calls."""
import asyncio
import httpx

class LLMUnavailable(Exception):
    """Raised when the LLM can't be reached after retries."""
    pass

def _is_retryable(exc: Exception) -> bool:
    """Decide whether an exception is worth retrying.
    
    Return True for: timeouts, network errors, 5xx responses, 429.
    Return False for everything else.
    """
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.NetworkError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code >= 500 or exc.response.status_code == 429:
            return True
    return False
    
async def call_with_retry(fn, max_attempts: int = 3, base_delay_s: float = 1.0):
    """Call fn() with retry on transient failures, exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except Exception as exc:
            if not _is_retryable(exc):
                # Non-retryable: re-raise the original exception unchanged
                raise
            if attempt == max_attempts:
                # Out of retries on a retryable error → genuine "unavailable"
                raise LLMUnavailable(f"LLM call failed after {attempt} attempts") from exc
            # Retryable + attempts remain → wait, then loop continues
            delay = base_delay_s * (2 ** (attempt - 1))
            await asyncio.sleep(delay)
    