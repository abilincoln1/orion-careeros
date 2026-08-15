"""Aggregates all v1 routers. New services register here as they're built."""
from fastapi import APIRouter

from app.api.v1 import auth, health
from app.api.v1 import document_intelligence
from app.api.v1 import job_discovery
from app.api.v1.career_dna import router as career_dna_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(career_dna_router)
api_router.include_router(document_intelligence.router)
api_router.include_router(job_discovery.router)
