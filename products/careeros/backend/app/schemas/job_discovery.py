"""Pydantic schemas for the Job Discovery API surface."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    """Every field optional -- per-request overrides for what Career DNA
    can't yet supply (no LocationPreference/SalaryPreference write path
    exists), falling back to config defaults if omitted. See
    docs/LEAN-JOB-DISCOVERY-IMPLEMENTATION-PLAN.md."""

    location: Optional[str] = Field(default=None, max_length=200)
    remote_only: Optional[bool] = None
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)


class JobListingRead(BaseModel):
    id: uuid.UUID
    title: str
    company_name_raw: str
    location_raw: Optional[str] = None
    is_remote: bool
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_disclosed: bool
    description_raw: Optional[str] = None
    source_url: str
    posted_at: Optional[datetime] = None
    discovered_at: datetime

    model_config = {"from_attributes": True}


class DiscoveryResponse(BaseModel):
    provider_name: str
    query_used: str
    listings_found: int
    listings_new: int
    listings_duplicate: int


class JobListingPage(BaseModel):
    items: list[JobListingRead]
    total: int
    limit: int
    offset: int
