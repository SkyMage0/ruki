"""FastAPI app: health, metrics, admin. Sentry + CORS + middleware."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routes import admin, health, metrics
from core.config import get_settings
from core.monitoring import (
    configure_logging,
    get_logger,
    http_requests_total,
    init_sentry,
    request_duration_seconds,
)
from core.redis_client import close_redis

configure_logging()
init_sentry()
logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(title="Ruki API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path or "/"
    http_requests_total.labels(method=request.method, endpoint=endpoint).inc()
    request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(duration)
    return response


app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"service": "ruki-api", "docs": "/docs"}
