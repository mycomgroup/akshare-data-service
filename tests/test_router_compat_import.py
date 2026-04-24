"""Compatibility tests for legacy router import path."""

import pytest

from akshare_data.ingestion.router import (
    DomainRateLimiter as CoreDomainRateLimiter,
    MultiSourceRouter as CoreMultiSourceRouter,
)
from akshare_data.sources.router import (
    DomainRateLimiter as CompatDomainRateLimiter,
    MultiSourceRouter as CompatMultiSourceRouter,
)

pytestmark = pytest.mark.unit


def test_router_compat_imports_point_to_core_impl():
    """Legacy sources.router imports should resolve to ingestion.router classes."""
    assert CompatDomainRateLimiter is CoreDomainRateLimiter
    assert CompatMultiSourceRouter is CoreMultiSourceRouter
