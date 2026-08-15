"""Job Discovery endpoints (MVP Priority 2 slice)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person, get_job_provider
from app.core.database import get_db
from app.job_discovery import discovery_service
from app.job_discovery.provider import JobProviderFetchError
from app.models.person import Person
from app.schemas.job_discovery import DiscoveryRequest, DiscoveryResponse, JobListingPage

router = APIRouter(prefix="/job-discovery", tags=["job-discovery"])


@router.post("/discover", response_model=DiscoveryResponse, status_code=status.HTTP_200_OK)
async def discover_jobs(
    request: DiscoveryRequest = DiscoveryRequest(),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
    provider=Depends(get_job_provider),
):
    try:
        result = await discovery_service.discover(
            db,
            current_person,
            provider,
            location_override=request.location,
            remote_only_override=request.remote_only,
            salary_min_override=request.salary_min,
            salary_max_override=request.salary_max,
        )
    except JobProviderFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Job provider request failed: {exc}",
        )

    return DiscoveryResponse(
        provider_name=result.provider_name,
        query_used=result.criteria.query,
        listings_found=result.listings_found,
        listings_new=result.listings_new,
        listings_duplicate=result.listings_duplicate,
    )


@router.get("/listings", response_model=JobListingPage)
async def list_job_listings(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    """Requires authentication (consistent with every other endpoint in
    this API), but listings themselves are a shared catalogue, not
    person-owned data -- see discovery_service.discover's ownership
    note. Every authenticated person sees the same listings."""
    items, total = await discovery_service.list_listings(db, limit=limit, offset=offset)
    return JobListingPage(items=items, total=total, limit=limit, offset=offset)
