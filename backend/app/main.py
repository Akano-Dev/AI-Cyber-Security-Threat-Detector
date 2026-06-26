"""ACSTD FastAPI application — API-first (/api/v1) with auth, logging, hardening."""
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core import state
from app.core.logging import logger, setup_logging
from app.core.metrics import metrics
from app.db import database, repository
from app.ml import pipeline
from app.schemas import ReadinessResponse

OPENAPI_TAGS = [
    {"name": "meta", "description": "Health, readiness, version, and runtime metrics."},
    {"name": "detection", "description": "Classify a single payload."},
    {"name": "threats", "description": "Threat log, block/ignore actions, CSV export, demo reset."},
    {"name": "stats", "description": "Aggregate counts and ML model metadata."},
    {"name": "config", "description": "Proxy + rate-limit configuration (admin)."},
    {"name": "proxy", "description": "Inline inspecting reverse proxy."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    database.init_db()
    state.blocklist.update(repository.load_blocked_ips())
    loaded = pipeline.load()
    logger.info("Loaded %d blocked IP(s) from database.", len(state.blocklist))
    logger.info("ML model loaded." if loaded else "WARNING: model.pkl not found — run training first.")
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI Cyber Security Threat Detector — real-time web threat detection API.",
    version=settings.app_version,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.max_body_bytes:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    """Assign a request id, time the request, and record runtime metrics."""
    request.state.request_id = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        metrics.observe(500, (time.perf_counter() - start) * 1000)
        raise  # let the handler below build the response
    elapsed_ms = (time.perf_counter() - start) * 1000
    metrics.observe(response.status_code, elapsed_ms)
    response.headers["X-Request-ID"] = request.state.request_id
    if elapsed_ms > 1000:
        logger.warning("slow %s %s -> %s in %.0fms [%s]",
                       request.method, request.url.path, response.status_code,
                       elapsed_ms, request.state.request_id)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "-")
    logger.exception("Unhandled error on %s %s [%s]", request.method, request.url.path, request_id)
    return JSONResponse({"detail": "Internal server error", "request_id": request_id}, status_code=500)


@app.get("/health", tags=["meta"], summary="Liveness probe")
def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["meta"], response_model=ReadinessResponse,
         summary="Readiness probe with component diagnostics")
def health_ready(response: Response):
    """Check DB connectivity and model load state. Returns 503 if the DB is unreachable."""
    db_ok = database.healthcheck()
    model_ok = pipeline.is_ready()
    if not db_ok:
        response.status_code = 503
    return {"status": "ok" if (db_ok and model_ok) else "degraded",
            "checks": {"database": db_ok, "model_loaded": model_ok}}


app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
