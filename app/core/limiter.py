from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

# IPs that bypass rate limiting (internal tooling, eval scripts, health checks)
EXEMPT_IPS = {"127.0.0.1", "::1", "localhost"}


def key_func(request: Request) -> str | None:
    """
    Rate-limit key function.

    Returns None for exempt IPs (which tells slowapi to skip limiting),
    otherwise returns the remote address as the key.
    """
    remote = get_remote_address(request)
    if remote in EXEMPT_IPS:
        return None
    return remote


limiter = Limiter(key_func=key_func, default_limits=["5/minute"])
