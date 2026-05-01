"""Legacy source compatibility adapter for online read-only API.

This module keeps backward-compatible source-proxy interfaces, but online API
remains read-only: no synchronous source pull and no cache writes.

.. deprecated::
    This module is deprecated since 0.3.0. Use the Served layer via
    ``DataService.query()`` instead. Will be removed in 0.4.0.
"""

from __future__ import annotations

import logging
import warnings

logger = logging.getLogger("akshare_data")

__deprecated__ = True


class SourceProxy:
    """Dynamic proxy for source method dispatch.

    Captures method calls and delegates to DataService._execute_source_method.
    Used for backward compatibility with source-based fetching patterns.
    """

    def __init__(self, service, requested_source=None):
        self.service = service
        self.requested_source = requested_source

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            return self.service._execute_source_method(
                name, self.requested_source, *args, **kwargs
            )

        return wrapper


class _DeprecatedSourceAdapterHandle:
    """Deprecated source adapter handle. Do NOT use in new code.

    Only accessible via ``DataService._legacy`` for migration/testing purposes.
    Use the Served layer via ``DataService.query()`` instead.

    .. deprecated:: 0.3.0
        Will be removed in 0.4.0.
    """

    def __init__(self, router=None, access_logger=None, source=None):
        warnings.warn(
            "_DeprecatedSourceAdapterHandle is deprecated. "
            "Use the Served layer via DataService.query() instead. "
            "Deprecated since 0.3.0, will be removed in 0.4.0.",
            DeprecationWarning,
            stacklevel=3,
        )
        self.router = router
        self.access_logger = access_logger
        self._custom_source = source

        if router is not None:
            logger.warning(
                "router parameter is deprecated in read-only mode; source adapters are not used"
            )
        if source is not None:
            logger.warning(
                "source parameter is deprecated in read-only mode; source adapters are not used"
            )

        if source is not None:
            self.adapters = {source.name: source}
            self.lixinger = source
            self.akshare = source
            return

        from akshare_data.ingestion.adapters.mock import MockAdapter

        mock = MockAdapter()
        self.adapters = {"mock": mock}
        self.lixinger = mock
        self.akshare = mock

    def _execute_source_method(self, method_name, requested_source, *args, **kwargs):
        """Execute a method on the specified source adapter."""
        if self.akshare is not None and hasattr(self.akshare, method_name):
            return getattr(self.akshare, method_name)(*args, **kwargs)

        if self.lixinger is not None and hasattr(self.lixinger, method_name):
            return getattr(self.lixinger, method_name)(*args, **kwargs)

        if self._custom_source is not None and hasattr(self._custom_source, method_name):
            return getattr(self._custom_source, method_name)(*args, **kwargs)

        if self.router is not None:
            try:
                result = self.router.execute(method_name, *args, **kwargs)
                if result.success:
                    return result.data
            except Exception:
                pass

        logger.warning(
            f"_execute_source_method: no matching source for '{method_name}' "
            f"(requested_source={requested_source})"
        )
        return None

    def _resolve_sources(self, requested_source, method_name):
        """Resolve which source(s) to use for a given method."""
        if requested_source is not None:
            if isinstance(requested_source, list):
                return requested_source
            return [requested_source]

        available = list(self.adapters.keys())
        if available:
            return available
        return ["mock"]


