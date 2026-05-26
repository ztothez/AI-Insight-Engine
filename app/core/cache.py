"""Redis caching layer for /analyze responses."""
import hashlib
import json
import os
from typing import Any

import redis.asyncio as redis
from loguru import logger

def get_redis_client():
    """Create a Redis client from REDIS_URL environment variable."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

def make_cache_key(code_snippet: str, language: str, strictness_level: int) -> str:
    """Generate a deterministic cache key from the request parameters."""
    key_string = f"{language}:{strictness_level}:{code_snippet}"
    return "analyze:" + hashlib.sha256(key_string.encode("utf-8")).hexdigest()

async def get_cached(client, key: str) -> dict | None:
    """Get a cached response. Returns None on miss or error."""
    try:
        cached = await client.get(key)
        if cached is not None:
            return json.loads(cached)
    except Exception as exc:
        logger.warning(f"Cache get error for key {key}: {exc}")
    return None


async def set_cached(client, key: str, value: dict, ttl_seconds: int = 3600) -> None:
    """Cache a response with TTL. Never raises — cache failure shouldn't break the request."""
    try:
        await client.setex(key, ttl_seconds, json.dumps(value))
    except Exception as exc:
        logger.warning(f"Cache set error for key {key}: {exc}")