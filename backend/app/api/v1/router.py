"""Aggregate all v1 routers under a single APIRouter."""
from fastapi import APIRouter

from app.api.v1 import analyze, config, meta, proxy, stats, threats, ws

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(analyze.router)
api_router.include_router(threats.router)
api_router.include_router(config.router)
api_router.include_router(stats.router)
api_router.include_router(proxy.router)
api_router.include_router(ws.router)
