"""
CareerOS logging setup.

Thin wrapper around the ORION Platform Kernel's logging module
(platform/kernel/orion_kernel/logging.py), bound to CareerOS's own
Settings instance. All product logging behavior (JSON vs plain-text,
level, request-context fields) is defined once, in the kernel, so every
future ORION product gets identical logging semantics for free.
"""
from orion_kernel.logging import configure_logging as _kernel_configure_logging
from orion_kernel.logging import get_logger  # re-exported for app-local use

from app.core.config import get_settings


def configure_logging() -> None:
    _kernel_configure_logging(get_settings())


__all__ = ["configure_logging", "get_logger"]
