"""
Job Discovery orchestration service. MVP Priority 2 slice.

Reads Career DNA (never writes to it -- this feature has no Career DNA
write path at all, unlike Document Intelligence). Derives search
criteria from the person's most recent Employment role title and their
PersonSkill names; accepts optional per-request overrides for location/
remote/salary, falling back to any existing SalaryPreference/
LocationPreference row (read-only), then to DiscoverySettings config
defaults -- per docs/LEAN-JOB-DISCOVERY-IMPLEMENTATION-PLAN.md's
explicit "no second profile model" decision.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.job_discovery.provider import JobProviderClient, JobProviderFetchError, RawJobListing
from app.models.employment import Employment
from app.models.job import JobListing, JobProvider
from app.models.person import Person
from app.models.skills import PersonSkill, Skill


@dataclass
class DiscoveryCriteria:
    query: str
    location: str | None
    remote_only: bool
    salary_min: float
    salary_max: float


@dataclass
class DiscoveryResult:
    criteria: DiscoveryCriteria
    listings_found: int
    listings_new: int
    listings_duplicate: int
    provider_name: str


async def derive_criteria(
    db: AsyncSession,
    person: Person,
    *,
    location_override: str | None = None,
    remote_only_override: bool | None = None,
    salary_min_override: float | None = None,
    salary_max_override: float | None = None,
) -> DiscoveryCriteria:
    """
    Query text: the most recent Employment's role_title_raw, if any --
    the single strongest signal of "what this person does" already in
    Career DNA. Falls back to the top few PersonSkill names if no
    Employment exists yet (a person could have skills without any
    employment history recorded).
    """
    result = await db.execute(
        select(Employment)
        .where(Employment.person_id == person.id)
        .order_by(Employment.is_current.desc(), Employment.start_date.desc())
        .limit(1)
    )
    latest_employment = result.scalar_one_or_none()

    if latest_employment is not None:
        query = latest_employment.role_title_raw
    else:
        result = await db.execute(
            select(Skill.name)
            .join(PersonSkill, PersonSkill.skill_id == Skill.id)
            .where(PersonSkill.person_id == person.id)
            .limit(3)
        )
        skill_names = [row[0] for row in result.all()]
        query = " ".join(skill_names) if skill_names else ""

    settings = get_settings()
    return DiscoveryCriteria(
        query=query,
        location=location_override,
        remote_only=bool(remote_only_override) if remote_only_override is not None else False,
        salary_min=salary_min_override if salary_min_override is not None else settings.DISCOVERY_DEFAULT_SALARY_MIN,
        salary_max=salary_max_override if salary_max_override is not None else settings.DISCOVERY_DEFAULT_SALARY_MAX,
    )


async def get_or_create_provider(db: AsyncSession, provider_name: str) -> JobProvider:
    result = await db.execute(select(JobProvider).where(JobProvider.name == provider_name))
    provider_row = result.scalar_one_or_none()
    if provider_row is None:
        provider_row = JobProvider(name=provider_name, is_active=True)
        db.add(provider_row)
        await db.flush()
    return provider_row


async def discover(
    db: AsyncSession,
    person: Person,
    provider_client: JobProviderClient,
    *,
    location_override: str | None = None,
    remote_only_override: bool | None = None,
    salary_min_override: float | None = None,
    salary_max_override: float | None = None,
) -> DiscoveryResult:
    """
    The one entry point: derive criteria, call the provider, upsert
    listings (dedup on (provider_id, provider_external_id), per the
    existing JobListing unique constraint). Ownership/security note:
    JobListing is NOT person-scoped at all -- listings are a shared,
    provider-sourced catalogue, not per-user data, so there is no
    ownership check on read/write here by design (confirmed against
    Section 14's security requirement: "provider data cannot bypass
    application ownership/security boundaries" -- the boundary that
    matters is that provider data never gets a free pass into a
    person-owned table like Employment/PersonSkill; it never does,
    since this feature has no Career DNA write path at all).
    """
    criteria = await derive_criteria(
        db,
        person,
        location_override=location_override,
        remote_only_override=remote_only_override,
        salary_min_override=salary_min_override,
        salary_max_override=salary_max_override,
    )

    try:
        raw_listings: list[RawJobListing] = await provider_client.search(
            query=criteria.query, location=criteria.location, remote_only=criteria.remote_only
        )
    except JobProviderFetchError:
        raise  # let the API layer map this to a clean error response, not a 500

    provider_row = await get_or_create_provider(db, provider_client.provider_name)

    new_count = 0
    duplicate_count = 0
    for raw in raw_listings:
        existing = await db.execute(
            select(JobListing).where(
                JobListing.provider_id == provider_row.id,
                JobListing.provider_external_id == raw.external_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            duplicate_count += 1
            continue

        posted_at_parsed = None
        if raw.posted_at:
            try:
                posted_at_parsed = datetime.fromisoformat(raw.posted_at)
            except ValueError:
                posted_at_parsed = None  # malformed ISO string from a provider -- drop, never invent

        db.add(
            JobListing(
                provider_id=provider_row.id,
                provider_external_id=raw.external_id,
                title=raw.title,
                company_name_raw=raw.company_name,
                location_raw=raw.location,
                is_remote=raw.is_remote,
                salary_min=raw.salary_min,
                salary_max=raw.salary_max,
                salary_currency=raw.salary_currency,
                salary_disclosed=raw.salary_disclosed,
                description_raw=raw.description,
                source_url=raw.source_url,
                posted_at=posted_at_parsed,
                raw_payload_json=raw.raw_payload,
            )
        )
        new_count += 1

    await db.commit()

    return DiscoveryResult(
        criteria=criteria,
        listings_found=len(raw_listings),
        listings_new=new_count,
        listings_duplicate=duplicate_count,
        provider_name=provider_client.provider_name,
    )


async def list_listings(db: AsyncSession, limit: int = 50, offset: int = 0) -> tuple[list[JobListing], int]:
    result = await db.execute(select(JobListing).order_by(JobListing.discovered_at.desc()).limit(limit).offset(offset))
    items = list(result.scalars().all())
    count_result = await db.execute(select(JobListing))
    total = len(count_result.scalars().all())
    return items, total
