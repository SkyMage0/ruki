"""Health and readiness probes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Liveness: check DB and Redis."""
    status = {"status": "ok", "database": "unknown", "redis": "unknown"}
    try:
        await db.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["db_error"] = str(e)
    try:
        r = await get_redis()
        await r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = "error"
        status["redis_error"] = str(e)
    return status


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness for k8s/docker: DB must be up."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}
