"""
Career DNA Service API (Sprint 2 core slice). Aggregates the
person/employment/skill/evidence routers into one prefix.
"""
from fastapi import APIRouter

from app.api.v1.career_dna import employment, evidence, person, skill

router = APIRouter(prefix="/career-dna", tags=["career-dna"])
router.include_router(person.router)
router.include_router(employment.router)
router.include_router(skill.router)
router.include_router(evidence.router)
