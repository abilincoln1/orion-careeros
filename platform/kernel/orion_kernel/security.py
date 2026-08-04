"""
Platform Kernel: authentication primitives.

Password hashing (bcrypt) and JWT access/refresh token issuance and
verification, parametrized entirely by the calling product's settings
(secret key, algorithm, expiry) so no product hardcodes crypto policy --
it just supplies its Settings instance.

This module implements the "Authentication" responsibility of the
Platform Kernel described in docs/platform/PLATFORM_KERNEL.md.
Authorization (roles/permissions/scopes) is not yet implemented anywhere
on the platform -- see that document and docs/TechnicalDebt.md.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, expires_delta: timedelta, token_type: str, secret_key: str, algorithm: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_access_token(subject: str, settings) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        settings.SECRET_KEY,
        settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: str, settings) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
        settings.SECRET_KEY,
        settings.JWT_ALGORITHM,
    )


def decode_token(token: str, settings) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
