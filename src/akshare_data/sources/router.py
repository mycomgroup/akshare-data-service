"""Backward-compatible router exports.

The canonical implementation lives in ``akshare_data.ingestion.router``.
This module only re-exports those symbols to avoid breaking legacy imports.
"""

from akshare_data.ingestion.router import (
    DomainRateLimiter,
    EmptyDataPolicy,
    ExecutionResult,
    MultiSourceRouter,
    SourceHealthMonitor,
    create_simple_router,
)

__all__ = [
    "EmptyDataPolicy",
    "ExecutionResult",
    "DomainRateLimiter",
    "SourceHealthMonitor",
    "MultiSourceRouter",
    "create_simple_router",
]
