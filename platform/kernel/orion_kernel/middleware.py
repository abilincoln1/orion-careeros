"""
Platform Kernel: request-context middleware.

Attaches a request ID and structured timing/status log to every request,
for every product, identically.
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from orion_kernel.logging import get_logger

logger = get_logger("orion.kernel.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
