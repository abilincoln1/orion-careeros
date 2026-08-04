"""
CareerOS authentication: password hashing + JWT issuance/verification.

Thin wrapper around the ORION Platform Kernel's security primitives
(platform/kernel/orion_kernel/security.py), bound to CareerOS's own
Settings instance so call sites in app/api don't need to thread settings
through themselves.

Sprint 1 delivers the auth *framework* only (register/login/me, password
hashing, signed JWT access+refresh tokens). It intentionally does not yet
implement role-based authorization, SSO, or multi-tenant scoping -- those
arrive with the multi-user SaaS phase per the project mission. Role-based
authorization is a documented Platform Kernel responsibility
(docs/platform/PLATFORM_KERNEL.md) not yet implemented by any product.
"""
from orion_kernel.security import (
    create_access_token as _kernel_create_access_token,
)
from orion_kernel.security import (
    create_refresh_token as _kernel_create_refresh_token,
)
from orion_kernel.security import decode_token as _kernel_decode_token
from orion_kernel.security import hash_password, verify_password  # re-exported as-is

from app.core.config import get_settings


def create_access_token(subject: str) -> str:
    return _kernel_create_access_token(subject, get_settings())


def create_refresh_token(subject: str) -> str:
    return _kernel_create_refresh_token(subject, get_settings())


def decode_token(token: str) -> dict | None:
    return _kernel_decode_token(token, get_settings())


__all__ = ["hash_password", "verify_password", "create_access_token", "create_refresh_token", "decode_token"]
