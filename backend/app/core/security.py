"""Authentication + real client-IP resolution."""
from fastapi import Header, HTTPException, Request, status

from app.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Dependency that rejects requests without a valid X-API-Key header."""
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP, honouring X-Forwarded-For behind trusted proxies.

    TRUSTED_PROXY_COUNT = number of trusted proxies in front of the app. With 0
    (default) we trust the direct socket peer. With N we take the Nth entry from
    the right of X-Forwarded-For, which the trusted proxies appended — so a client
    cannot spoof its IP by sending its own X-Forwarded-For header.
    """
    n = settings.trusted_proxy_count
    if n > 0:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[-min(n, len(parts))]
    return request.client.host if request.client else "unknown"
