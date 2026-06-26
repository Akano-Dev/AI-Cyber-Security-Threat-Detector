"""GET/POST /config — read and update proxy + rate-limit settings (admin)."""
from fastapi import APIRouter, Depends

from app.config import apply_config_update, settings
from app.core.security import require_api_key
from app.schemas import ConfigUpdate

router = APIRouter(tags=["config"], dependencies=[Depends(require_api_key)])


@router.get("/config")
def get_config():
    return {
        "target_url": settings.target_url,
        "rate_limit": settings.rate_limit,
        "rate_window": settings.rate_window,
    }


@router.post("/config")
def update_config(cfg: ConfigUpdate):
    return apply_config_update(cfg.target_url, cfg.rate_limit, cfg.rate_window)
