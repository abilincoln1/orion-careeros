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
