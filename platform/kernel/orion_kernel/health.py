"""
Platform Kernel: health/readiness endpoint factory.

Every ORION product gets identical liveness/readiness semantics without
reimplementing them: /health (summary), /health/live (process is up),
/health/ready (checks the product's own DB connectivity via its get_db
dependency). Products call `build_health_router(...)` once and mount it.
"""
from typing import Callable

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from orion_kernel.database import check_database_connection


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ReadinessStatus(BaseModel):
    status: str
    database: str
    detail: str | None = None


def build_health_router(settings, get_db: Callable) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health", response_model=HealthStatus)
    async def health() -> HealthStatus:
        return HealthStatus(
            status="ok", service=settings.APP_NAME,
            version=settings.APP_VERSION, environment=settings.ENVIRONMENT,
        )

    @router.get("/health/live", response_model=HealthStatus)
    async def liveness() -> HealthStatus:
        return HealthStatus(
            status="alive", service=settings.APP_NAME,
            version=settings.APP_VERSION, environment=settings.ENVIRONMENT,
        )

    @router.get("/health/ready", response_model=ReadinessStatus)
    async def readiness(response: Response, db: AsyncSession = Depends(get_db)) -> ReadinessStatus:
        db_ok = await check_database_connection(db)
        if not db_ok:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return ReadinessStatus(status="not_ready", database="unreachable", detail="Database connection failed")
        return ReadinessStatus(status="ready", database="ok")

    return router
