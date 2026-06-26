"""Application settings, loaded from environment / .env (pydantic-settings)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

    # Service identity (surfaced by /version, /metrics, Swagger)
    app_name: str = "ACSTD API"
    app_version: str = "1.0.0"
    api_version: str = "v1"

    # Proxy target + rate limiting
    target_url: str = ""
    rate_limit: int = 20
    rate_window: int = 60

    # Security
    api_key: str = "acstd-dev-key"           # required by admin/mutating endpoints
    trusted_proxy_count: int = 0             # # of trusted proxies in front of the app
    max_body_bytes: int = 1_000_000          # reject request bodies larger than this

    # Paths
    db_path: str = str(BASE_DIR / "threats.db")
    model_path: str = str(BASE_DIR / "model.pkl")
    metrics_path: str = str(BASE_DIR / "metrics.json")

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()


def forward_base() -> str:
    """Target URL with any trailing slash removed."""
    return settings.target_url.rstrip("/")


def persist_env(updates: dict) -> None:
    """Write key=value pairs back to the .env file, preserving other lines."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    result, seen = [], set()
    for line in lines:
        key = line.split("=")[0].strip() if "=" in line and not line.startswith("#") else ""
        if key in updates:
            result.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            result.append(line)
    for k, v in updates.items():
        if k not in seen:
            result.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(result) + "\n", encoding="utf-8")


def apply_config_update(target_url=None, rate_limit=None, rate_window=None) -> dict:
    """Update runtime settings and persist them to .env."""
    updates = {}
    if target_url is not None:
        settings.target_url = target_url.rstrip("/")
        updates["TARGET_URL"] = target_url
    if rate_limit is not None:
        settings.rate_limit = rate_limit
        updates["RATE_LIMIT"] = str(rate_limit)
    if rate_window is not None:
        settings.rate_window = rate_window
        updates["RATE_WINDOW"] = str(rate_window)
    if updates:
        persist_env(updates)
    return {"target_url": settings.target_url, "rate_limit": settings.rate_limit, "rate_window": settings.rate_window}
