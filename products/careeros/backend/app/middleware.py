"""
CareerOS request middleware.

Re-exports the ORION Platform Kernel's RequestContextMiddleware
(platform/kernel/orion_kernel/middleware.py) so every ORION product
attaches request IDs and structured timing/status logs identically,
without each product reimplementing it.
"""
from orion_kernel.middleware import RequestContextMiddleware

__all__ = ["RequestContextMiddleware"]
