"""
CareerOS (Project ORION) -- FastAPI application entrypoint.

Sprint 1 scope only: platform foundation. No AI, scraping, matching, or
document generation logic lives here -- this file wires together config,
logging, database, auth framework, health monitoring, and the API router.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.middleware import RequestContextMiddleware

settings = get_settings()
configure_logging()
logger = get_logger("careeros.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    yield
    logger.info("Shutting down CareerOS backend")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Career Intelligence Platform API. Sprint 1: engineering foundation "
        "(auth, config, logging, health, persistence). See /docs for the "
        "interactive API reference."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": "Validation error", "details": exc.errors()}},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }
