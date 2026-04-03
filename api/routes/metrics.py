"""Prometheus /metrics endpoint."""
from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from core.monitoring import get_metrics_registry, active_users_gauge
from core.redis_client import get_active_users_count

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    try:
        count = await get_active_users_count()
        active_users_gauge.set(count)
    except Exception:
        pass
    return generate_latest(get_metrics_registry()), {"Content-Type": CONTENT_TYPE_LATEST}
