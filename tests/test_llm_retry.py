"""Unit tests for the LLM retry wrapper."""
import httpx
import pytest

from app.core.llm_retry import call_with_retry, LLMUnavailable


class TestSuccess:
    """Tests where the wrapped function eventually succeeds."""

    @pytest.mark.asyncio
    async def test_first_attempt_succeeds(self):
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await call_with_retry(fn)

        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_succeeds_after_one_retry(self):
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("first try fails")
            return "ok"

        result = await call_with_retry(fn, base_delay_s=0.01)

        assert result == "ok"
        assert call_count == 2


class TestRetryableFailures:
    """Tests where every attempt fails with a retryable error."""

    @pytest.mark.asyncio
    async def test_exhausts_retries_on_persistent_timeout(self):
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("always times out")

        with pytest.raises(LLMUnavailable):
            await call_with_retry(fn, max_attempts=3, base_delay_s=0.01)

        assert call_count == 3