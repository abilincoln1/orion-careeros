"""
CareerOS health monitoring endpoints.

Built from the ORION Platform Kernel's health router factory
(platform/kernel/orion_kernel/health.py) bound to CareerOS's own settings
and get_db dependency, so /health, /health/live, and /health/ready behave
identically across every ORION product without CareerOS reimplementing
them.
"""
from orion_kernel.health import build_health_router

from app.core.config import get_settings
from app.core.database import get_db

router = build_health_router(get_settings(), get_db)
