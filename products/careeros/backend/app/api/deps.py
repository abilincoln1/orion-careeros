"""Shared FastAPI dependencies: DB session and current-user resolution."""
import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def parse_user_id(raw: Optional[str]) -> Optional[uuid.UUID]:
    """
    Parse a JWT 'sub' claim into a User.id UUID, returning None on any
    malformed input instead of raising. Shared by both places a token's
    subject is resolved to a user (this dependency, and the /auth/refresh
    endpoint in app/api/v1/auth.py) -- previously duplicated inline in
    both, found during the Sprint 1 Closure repository review.
    """
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError, TypeError):
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_uuid = parse_user_id(payload.get("sub"))
    if user_uuid is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_person(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves the authenticated User to their Career DNA Person record.
    Every Career DNA endpoint (Sprint 2) scopes through this, never
    through a client-supplied person_id, so a person can only ever read
    or write their own Career DNA -- there is no code path in the Career
    DNA API that accepts another person's id.

    404s (not silently creates one) if the user hasn't called
    POST /career-dna/person yet -- see app/services/person_service.py
    for why Person creation is an explicit client action, not automatic
    at registration.
    """
    from app.services.person_service import get_person_or_404

    return await get_person_or_404(db, current_user.id)


def get_storage_adapter():
    """
    Returns the configured StorageAdapter -- LocalStorageAdapter for
    Stage 1 (ADR 0005 Decision 1). Not cached at module level as a
    singleton, since LocalStorageAdapter's __init__ just ensures the
    directory exists (cheap, idempotent) -- a real future StorageAdapter
    with a connection pool would warrant caching this the same way
    get_settings() is cached, but that's speculative for a filesystem
    adapter.
    """
    from orion_kernel.document_intelligence import LocalStorageAdapter

    from app.core.config import get_settings

    settings = get_settings()
    return LocalStorageAdapter(settings.DOCUMENT_STORAGE_PATH)


def get_extraction_provider():
    """
    Returns the configured DocumentExtractionProvider. Now
    DeterministicCVProvider (a real, rule-based, non-LLM parser) --
    per the 13 August 2026 directive's "Next Task -- Minimum Real-CV
    Extraction Capability", authorizing exactly this: a deterministic
    parser over an LLM, since the AI Provider Policy's "no production
    LLM provider" restriction does not prohibit deterministic
    extraction, and this closes Priority 1's real, previously
    disclosed limitation (extraction depended on a manually-curated
    fixture, not the actual uploaded file's content). This remains the
    ONE place that changes if an LLM provider is ever separately
    authorized; every caller depends on the DocumentExtractionProvider
    protocol, not this specific class.
    """
    from orion_kernel.document_intelligence import DeterministicCVProvider

    return DeterministicCVProvider()


def get_job_provider():
    """
    Returns the configured JobProviderClient. MVP: always
    ArbeitnowProvider -- one provider, per the directive's explicit
    "implement only one real provider initially" instruction. This is
    the ONE place that changes if a second provider is ever authorized.
    """
    from app.job_discovery.arbeitnow_provider import ArbeitnowProvider

    return ArbeitnowProvider()
