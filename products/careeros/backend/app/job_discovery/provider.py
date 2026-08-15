"""
Job provider abstraction (MVP Priority 2 slice). Deliberately CareerOS-
product-level, not Platform Kernel -- unlike Document Intelligence,
nothing about job-board integration is stated as a cross-product
capability in this directive, so it isn't speculatively placed in the
kernel (see ADR 0006's own reasoning for why Document Intelligence WAS
kernel-placed, and why that reasoning doesn't automatically extend
here: reuse is Document Intelligence's stated purpose; nothing states
that here).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class JobProviderFetchError(RuntimeError):
    """Raised when a provider fails to return results -- a network
    failure, a malformed response, or the provider explicitly signalling
    an error. Callers are expected to catch this and report it, not let
    it propagate as an unhandled 500 (per Section 14's 'provider
    failure' test requirement)."""


@dataclass
class RawJobListing:
    """The provider-agnostic shape job_discovery_service consumes.
    Every JobProviderClient implementation normalizes its own raw
    response into this shape -- this is the ONLY place provider-specific
    field names are known anywhere in the codebase, mirroring the same
    normalization boundary Document Intelligence's provider abstraction
    established."""

    external_id: str
    title: str
    company_name: str
    location: str | None
    is_remote: bool
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    salary_disclosed: bool
    description: str | None
    source_url: str
    posted_at: str | None  # ISO 8601 string or None; parsed by the caller
    raw_payload: dict = field(default_factory=dict)


class JobProviderClient(Protocol):
    provider_name: str

    async def search(
        self, query: str, location: str | None, remote_only: bool
    ) -> list[RawJobListing]:
        """Returns whatever the provider's API returns for this query --
        no filtering, scoring, or ranking here (that would be Matching
        Engine territory, explicitly out of scope). Raises
        JobProviderFetchError on failure."""
        ...

    async def health_check(self) -> bool: ...
