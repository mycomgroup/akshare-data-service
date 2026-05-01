"""Multi-source router for the ingestion layer.

Handles routing, failover, circuit breaking, and empty-data policies
across multiple source adapters.  Does NOT carry service-level semantics.

Enhanced with per-method source priorities, exponential backoff retries,
in-flight request deduplication, fast-path caching, and cache warming.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class EmptyDataPolicy(Enum):
    """Policy for handling empty results."""

    STRICT = "strict"
    RELAXED = "relaxed"
    BEST_EFFORT = "best_effort"


@dataclass
class ExecutionResult:
    """Result of a multi-source execution."""

    success: bool
    data: Optional[pd.DataFrame]
    source: Optional[str]
    error: Optional[str]
    attempts: int
    error_details: Optional[List[Tuple[str, str]]] = None
    is_empty: bool = False
    is_fallback: bool = False
    sources_tried: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RetryConfig:
    """Per-method retry configuration."""

    max_retries: int = 2
    backoff: float = 1.0
    backoff_factor: float = 2.0


# ---------------------------------------------------------------------------
# Default per-method source priorities (ported from analysis_v2)
# ---------------------------------------------------------------------------

_DEFAULT_METHOD_PRIORITY: Dict[str, List[str]] = {
    "get_daily_data": ["tushare", "lixinger", "eastmoney", "akshare", "efinance", "baostock", "tickflow"],
    "get_index_components": ["eastmoney", "akshare", "lixinger", "baostock"],
    "get_trading_days": ["akshare", "eastmoney", "lixinger", "tickflow", "baostock"],
    "get_securities_list": ["eastmoney", "akshare", "lixinger", "tickflow"],
    "get_security_info": ["lixinger", "eastmoney", "akshare", "tickflow"],
    "get_minute_data": ["eastmoney", "akshare", "tickflow"],
    "get_money_flow": ["akshare", "eastmoney", "lixinger"],
    "get_north_money_flow": ["akshare", "eastmoney", "lixinger"],
    "get_industry_stocks": ["akshare", "eastmoney", "lixinger"],
    "get_industry_mapping": ["akshare", "eastmoney", "lixinger"],
    "get_finance_indicator": ["akshare", "eastmoney", "lixinger", "tushare", "baostock"],
    "get_call_auction": ["tickflow", "eastmoney", "akshare"],
    "get_stock_valuation": ["akshare", "eastmoney", "tushare", "lixinger"],
    "get_index_valuation": ["akshare", "eastmoney", "lixinger"],
    "get_dividend": ["eastmoney", "lixinger", "tushare", "akshare"],
    "get_spot_em": ["eastmoney", "akshare"],
    "get_macro_raw": ["akshare", "lixinger"],
    "get_cpi_data": ["akshare", "lixinger"],
    "get_ppi_data": ["akshare", "lixinger"],
    "get_pmi_index": ["akshare", "lixinger"],
    "get_m2_supply": ["akshare", "lixinger"],
    "get_gdp": ["lixinger", "akshare"],
    "get_billboard_list": ["lixinger", "eastmoney", "akshare"],
    "get_st_stocks": ["eastmoney", "akshare", "lixinger"],
    "get_suspended_stocks": ["eastmoney", "akshare", "lixinger"],
}

# ---------------------------------------------------------------------------
# Default per-method retry config (ported from analysis_v2)
# ---------------------------------------------------------------------------

_DEFAULT_RETRY_CONFIG: Dict[str, RetryConfig] = {
    "get_daily_data": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_minute_data": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_money_flow": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_north_money_flow": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_finance_indicator": RetryConfig(max_retries=3, backoff=2.0, backoff_factor=2.0),
    "get_stock_valuation": RetryConfig(max_retries=3, backoff=2.0, backoff_factor=2.0),
    "get_index_valuation": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_dividend": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_index_components": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_trading_days": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
    "get_securities_list": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
    "get_security_info": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_spot_em": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
    "get_macro_raw": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
    "get_billboard_list": RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0),
    "get_st_stocks": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
    "get_suspended_stocks": RetryConfig(max_retries=1, backoff=0.5, backoff_factor=1.5),
}


# ---------------------------------------------------------------------------
# Domain-level rate limiter
# ---------------------------------------------------------------------------


class DomainRateLimiter:
    """Domain-level rate limiter that maps real domains to abstract rate limit keys.

    Loads domain-to-rate-key mapping from config and interval values from
    rate_limits config.  All rate limiting uses abstract keys
    (e.g. ``em_push2his``) rather than raw hostnames.
    """

    def __init__(
        self,
        intervals: Optional[Dict[str, float]] = None,
        domain_map: Optional[Dict[str, str]] = None,
        default_interval: float = 0.5,
    ):
        self._intervals = intervals or {}
        self._domain_map = domain_map or {}
        self._default_interval = default_interval
        self._last_request: Dict[str, float] = {}
        self._lock = threading.Lock()

    @classmethod
    def from_config(
        cls,
        domains_path: Optional[str] = None,
        rate_limits_path: Optional[str] = None,
        domains_data: Optional[Dict] = None,
        rate_limits_data: Optional[Dict] = None,
    ) -> "DomainRateLimiter":
        import yaml

        if domains_data is None:
            if domains_path is None:
                raise ValueError("Need either domains_path or domains_data")
            with open(domains_path, "r") as f:
                domains_data = yaml.safe_load(f)

        if rate_limits_data is None:
            if rate_limits_path is None:
                raise ValueError("Need either rate_limits_path or rate_limits_data")
            with open(rate_limits_path, "r") as f:
                rate_limits_data = yaml.safe_load(f)

        domain_map: Dict[str, str] = {}
        domains_section = domains_data.get("domains", domains_data)
        for key, value in domains_section.items():
            if isinstance(value, dict):
                rate_key = value.get("rate_limit_key", key)
                url_pattern = value.get("url_pattern")
                if url_pattern:
                    domain_map[url_pattern] = rate_key

        intervals: Dict[str, float] = {}
        for key, value in rate_limits_data.items():
            if isinstance(value, dict):
                intervals[key] = value.get("interval", 0.5)
            elif isinstance(value, (int, float)):
                intervals[key] = value

        default_interval = intervals.get("default", 0.5)
        return cls(
            intervals=intervals,
            domain_map=domain_map,
            default_interval=default_interval,
        )

    def _resolve_rate_key(self, domain: str) -> str:
        if domain in self._domain_map:
            return self._domain_map[domain]
        if domain in self._intervals:
            return domain
        for pattern, key in self._domain_map.items():
            if pattern in domain or domain in pattern:
                return key
        return "default"

    def wait_if_needed(self, domain: str) -> None:
        rate_key = self._resolve_rate_key(domain)
        interval = self._intervals.get(rate_key, self._default_interval)
        with self._lock:
            last_time = self._last_request.get(rate_key, 0)
            elapsed = time.time() - last_time
            if elapsed < interval:
                sleep_time = interval - elapsed
                logger.debug("Rate limit %s: sleeping %.2fs", rate_key, sleep_time)
                time.sleep(sleep_time)
            self._last_request[rate_key] = time.time()

    def record_request(self, domain: str) -> None:
        rate_key = self._resolve_rate_key(domain)
        with self._lock:
            self._last_request[rate_key] = time.time()

    def set_interval(self, rate_key: str, interval: float) -> None:
        with self._lock:
            self._intervals[rate_key] = interval

    def get_interval(self, domain: str) -> float:
        rate_key = self._resolve_rate_key(domain)
        return self._intervals.get(rate_key, self._default_interval)

    def get_rate_key(self, domain: str) -> str:
        return self._resolve_rate_key(domain)

    def reset(self) -> None:
        with self._lock:
            self._last_request.clear()

    @staticmethod
    def extract_domain(url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url


# ---------------------------------------------------------------------------
# Source health monitor with circuit breaker
# ---------------------------------------------------------------------------


class SourceHealthMonitor:
    """Monitor health of data sources with a simple circuit breaker."""

    _ERROR_THRESHOLD = 5
    _DISABLE_DURATION = 300

    def __init__(self):
        self._status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record_result(
        self, source: str, success: bool, error: Optional[str] = None
    ) -> None:
        with self._lock:
            if source not in self._status:
                self._status[source] = {
                    "available": True,
                    "last_error": None,
                    "error_count": 0,
                }
            status = self._status[source]
            if success:
                status["available"] = True
                status["error_count"] = 0
                status["last_error"] = None
            else:
                status["error_count"] += 1
                status["last_error"] = error
                if status["error_count"] >= self._ERROR_THRESHOLD:
                    status["available"] = False
                    status["disabled_at"] = time.time()
                    logger.warning(
                        "Source %s temporarily disabled (too many errors)", source
                    )

    def is_available(self, source: str) -> bool:
        with self._lock:
            if source not in self._status:
                return True
            status = self._status[source]
            if not status["available"]:
                disabled_at = status.get("disabled_at")
                if disabled_at is not None:
                    elapsed = time.time() - disabled_at
                    if elapsed > self._DISABLE_DURATION:
                        status["available"] = True
                        status["error_count"] = 0
                        logger.info("Source %s recovered", source)
            return status["available"]

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        import copy

        with self._lock:
            return copy.deepcopy(self._status)


# ---------------------------------------------------------------------------
# Multi-source router
# ---------------------------------------------------------------------------


class MultiSourceRouter:
    """Routes data requests across multiple source adapters with automatic failover.

    Accepts a list of ``(name, adapter_instance)`` tuples or ``(name, callable)``
    tuples.  Each callable/adapter method should return a ``pd.DataFrame`` or
    raise an exception on failure.

    Responsibilities:
    - Try providers in priority order
    - Skip unavailable providers (circuit breaker)
    - Validate results
    - Apply empty-data policy
    - Track statistics

    Enhanced features (ported from analysis_v2):
    - Per-method source priorities
    - Exponential backoff retries
    - In-flight request deduplication
    - Fast-path caching (remember last successful source per method)
    - Cache warming interface
    """

    def __init__(
        self,
        providers: List[Tuple[str, Callable]],
        required_columns: Optional[List[str]] = None,
        min_rows: int = 0,
        policy: EmptyDataPolicy = EmptyDataPolicy.STRICT,
        stats_collector=None,
        method_priority: Optional[Dict[str, List[str]]] = None,
        method_retry_config: Optional[Dict[str, RetryConfig]] = None,
        cache_ttl: int = 3600,
    ):
        self.providers = list(providers)
        self.required_columns = required_columns or []
        self.min_rows = min_rows
        self.policy = policy
        self._health = SourceHealthMonitor()
        self._stats_collector = stats_collector
        self._stats: Dict[str, Any] = {
            "total_calls": 0,
            "successes": 0,
            "failures": 0,
            "empty_results": 0,
            "fallbacks": 0,
            "source_stats": {},
        }

        # Enhanced features from analysis_v2
        self._method_priority = method_priority or {}
        self._method_retry_config = method_retry_config or {}
        self._first_working_source: Dict[str, str] = {}
        self._inflight_lock = threading.Lock()
        self._inflight: Dict[str, threading.Event] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = cache_ttl
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_lock = threading.Lock()

    def warm(self, entries: Dict[str, Any]) -> int:
        """Warm cache with pre-computed entries.

        Args:
            entries: Dict[cache_key, data] to preload into memory cache.

        Returns:
            Number of entries warmed.
        """
        count = 0
        with self._cache_lock:
            for key, data in entries.items():
                if data is not None:
                    if isinstance(data, pd.DataFrame) and data.empty:
                        continue
                    self._cache[key] = data
                    self._cache_timestamps[key] = time.time()
                    count += 1
        logger.info("Warmed %d cache entries", count)
        return count

    def invalidate_cache(self, key: Optional[str] = None) -> int:
        """Invalidate memory cache entries.

        Args:
            key: Specific key to invalidate, or None to clear all.

        Returns:
            Number of entries invalidated.
        """
        with self._cache_lock:
            self._first_working_source.clear()
            if key is None:
                count = len(self._cache)
                self._cache.clear()
                self._cache_timestamps.clear()
                return count
            if key in self._cache:
                del self._cache[key]
                del self._cache_timestamps[key]
                return 1
            return 0

    def _get_cache(self, key: str) -> Optional[Any]:
        with self._cache_lock:
            if key not in self._cache:
                return None
            ts = self._cache_timestamps.get(key, 0)
            if time.time() - ts > self._cache_ttl:
                del self._cache[key]
                del self._cache_timestamps[key]
                return None
            return self._cache[key]

    def _put_cache(self, key: str, data: Any) -> None:
        with self._cache_lock:
            self._cache[key] = data
            self._cache_timestamps[key] = time.time()

    def _register_inflight(self, key: str) -> Optional[threading.Event]:
        """Register key as in-flight. Returns Event if this thread should fetch, None if another is already fetching."""
        with self._inflight_lock:
            if key in self._inflight:
                return None
            event = threading.Event()
            self._inflight[key] = event
            return event

    def _wait_inflight(self, key: str) -> None:
        with self._inflight_lock:
            event = self._inflight.get(key)
        if event:
            event.wait(timeout=30.0)

    def _unregister_inflight(self, key: str) -> None:
        with self._inflight_lock:
            event = self._inflight.pop(key, None)
        if event:
            event.set()

    def _make_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate a deterministic cache key for a method call."""
        try:
            args_repr = repr(args) + repr(sorted(kwargs.items()))
        except Exception:
            args_repr = repr(args) + repr(kwargs)
        return f"{method_name}:{hash(args_repr) & 0xFFFFFFFF}"

    def _get_retry_config(self, method_name: str) -> RetryConfig:
        return self._method_retry_config.get(method_name, RetryConfig(max_retries=2, backoff=1.0, backoff_factor=2.0))

    def _get_sources_for_method(self, method_name: str) -> List[str]:
        """Get ordered list of source names for a method, falling back to all providers."""
        if method_name in self._method_priority:
            priority = self._method_priority[method_name]
            # Filter to only available providers
            available = {name for name, _ in self.providers}
            return [s for s in priority if s in available]
        return [name for name, _ in self.providers]

    def execute_method(
        self,
        method_name: str,
        *args,
        **kwargs,
    ) -> ExecutionResult:
        """Execute a named method across providers with full enhancement.

        Features:
        - Method-level source priority
        - In-flight request deduplication
        - Memory cache (TTL)
        - Fast-path (remember last successful source)
        - Exponential backoff retry per source
        """
        self._stats["total_calls"] += 1
        cache_key = self._make_cache_key(method_name, *args, **kwargs)

        # 1. Check memory cache
        cached = self._get_cache(cache_key)
        if cached is not None:
            return ExecutionResult(
                success=True,
                data=cached,
                source="__cache__",
                error=None,
                attempts=0,
                is_fallback=False,
                sources_tried=[],
            )

        # 2. Deduplicate in-flight requests
        event = self._register_inflight(cache_key)
        if event is None:
            self._wait_inflight(cache_key)
            cached = self._get_cache(cache_key)
            if cached is not None:
                return ExecutionResult(
                    success=True,
                    data=cached,
                    source="__cache__",
                    error=None,
                    attempts=0,
                    is_fallback=False,
                    sources_tried=[],
                )
            # Another thread failed — fall through to execute

        try:
            sources = self._get_sources_for_method(method_name)
            retry_cfg = self._get_retry_config(method_name)
            error_details: List[Tuple[str, str]] = []
            sources_tried: List[Dict[str, Any]] = []

            # 3. Fast path: try last successful source first
            fast_source = self._first_working_source.get(method_name)
            if fast_source is not None and fast_source in sources:
                if self._health.is_available(fast_source):
                    result = self._try_source_with_retry(
                        fast_source, method_name, retry_cfg, *args, **kwargs
                    )
                    if result is not None and self._validate_result(result):
                        self._put_cache(cache_key, result)
                        return ExecutionResult(
                            success=True,
                            data=result,
                            source=fast_source,
                            error=None,
                            attempts=1,
                            is_fallback=False,
                            sources_tried=sources_tried,
                        )
                # Fast path failed — remove cached preference
                del self._first_working_source[method_name]

            # 4. Try each source in priority order
            for source_name in sources:
                if source_name == fast_source:
                    continue
                if not self._health.is_available(source_name):
                    logger.debug("Provider %s is unavailable, skipping", source_name)
                    continue

                start = time.time()
                source_info = {
                    "name": source_name,
                    "attempted": True,
                    "success": False,
                    "error": None,
                    "elapsed": 0.0,
                }

                result = self._try_source_with_retry(
                    source_name, method_name, retry_cfg, *args, **kwargs
                )
                elapsed = time.time() - start
                source_info["elapsed"] = elapsed

                if result is not None and self._validate_result(result):
                    self._first_working_source[method_name] = source_name
                    self._put_cache(cache_key, result)
                    self._update_stats(
                        source_name,
                        success=True,
                        empty=False,
                        fallback=len(sources_tried) > 0,
                        duration_ms=elapsed * 1000,
                    )
                    source_info["success"] = True
                    sources_tried.append(source_info)
                    return ExecutionResult(
                        success=True,
                        data=result,
                        source=source_name,
                        error=None,
                        attempts=len(sources_tried),
                        is_fallback=len(sources_tried) > 0,
                        sources_tried=sources_tried,
                    )

                source_info["error"] = "empty_or_invalid"
                sources_tried.append(source_info)
                self._health.record_result(source_name, success=False, error="empty_or_invalid")
                self._update_stats(
                    source_name,
                    success=False,
                    empty=False,
                    fallback=False,
                    duration_ms=elapsed * 1000,
                )

            # No provider returned valid data
            self._stats["failures"] += 1
            return ExecutionResult(
                success=False,
                data=None,
                source=None,
                error="all_providers_failed",
                attempts=len(sources_tried),
                error_details=error_details,
                is_empty=True,
                is_fallback=False,
                sources_tried=sources_tried,
            )

        finally:
            self._unregister_inflight(cache_key)

    def _try_source_with_retry(
        self,
        source_name: str,
        method_name: str,
        retry_cfg: RetryConfig,
        *args,
        **kwargs,
    ) -> Optional[Any]:
        """Try a single source with retries and backup methods."""
        # Find the provider callable
        func = None
        for name, f in self.providers:
            if name == source_name:
                func = f
                break
        if func is None:
            return None

        # Check if the source has the method as an attribute
        if hasattr(func, method_name):
            method = getattr(func, method_name)
        else:
            # Fallback: the provider itself is callable (legacy mode)
            method = func

        for attempt in range(retry_cfg.max_retries + 1):
            try:
                result = method(*args, **kwargs)
                if result is not None:
                    if isinstance(result, pd.DataFrame) and not result.empty:
                        self._health.record_result(source_name, success=True)
                        return result
                    if not isinstance(result, pd.DataFrame):
                        self._health.record_result(source_name, success=True)
                        return result
                # Empty result — don't retry, just return None
                return None
            except Exception as e:
                if attempt < retry_cfg.max_retries:
                    sleep_time = retry_cfg.backoff * (retry_cfg.backoff_factor ** attempt)
                    logger.debug(
                        "Provider %s.%s failed (attempt %d/%d), retrying in %.2fs: %s",
                        source_name,
                        method_name,
                        attempt + 1,
                        retry_cfg.max_retries + 1,
                        sleep_time,
                        e,
                    )
                    time.sleep(sleep_time)
                else:
                    self._health.record_result(source_name, success=False, error=str(e))
                    logger.warning(
                        "Provider %s.%s failed after %d attempts: %s",
                        source_name,
                        method_name,
                        retry_cfg.max_retries + 1,
                        e,
                    )
                    return None
        return None

    def execute(self, *args, **kwargs) -> ExecutionResult:
        """Execute a data fetch across providers with automatic failover.

        Legacy entry point — tries each provider in order without method-level
        priority or retry logic.  Use ``execute_method()`` for enhanced routing.
        """
        self._stats["total_calls"] += 1
        error_details: List[Tuple[str, str]] = []
        sources_tried: List[Dict[str, Any]] = []
        last_result: Optional[pd.DataFrame] = None
        last_source: Optional[str] = None
        last_empty = False

        for name, func in self.providers:
            if not self._health.is_available(name):
                logger.debug("Provider %s is unavailable, skipping", name)
                continue

            source_info = {
                "name": name,
                "attempted": False,
                "success": False,
                "error": None,
                "elapsed": 0.0,
            }
            source_info["attempted"] = True
            start = time.time()

            try:
                logger.debug("Trying provider: %s", name)
                data = func(*args, **kwargs)
                elapsed = time.time() - start
                source_info["elapsed"] = elapsed
                self._health.record_result(name, success=True)

                if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                    logger.debug("Provider %s returned empty data", name)
                    source_info["success"] = True
                    sources_tried.append(source_info)
                    last_result = data if isinstance(data, pd.DataFrame) else None
                    last_source = name
                    last_empty = True
                    continue

                if not self._validate_result(data):
                    logger.debug("Provider %s returned invalid data", name)
                    source_info["error"] = "validation_failed"
                    sources_tried.append(source_info)
                    continue

                is_fallback = len(sources_tried) > 0 or name == "__cache__"
                self._update_stats(
                    name,
                    success=True,
                    empty=False,
                    fallback=is_fallback,
                    duration_ms=elapsed * 1000,
                )
                source_info["success"] = True
                sources_tried.append(source_info)

                return ExecutionResult(
                    success=True,
                    data=data,
                    source=name,
                    error=None,
                    attempts=len(sources_tried),
                    error_details=error_details,
                    is_empty=False,
                    is_fallback=is_fallback,
                    sources_tried=sources_tried,
                )

            except Exception as e:
                elapsed = time.time() - start
                source_info["elapsed"] = elapsed
                source_info["error"] = str(e)
                sources_tried.append(source_info)
                error_details.append((name, str(e)))
                logger.warning("Provider %s failed: %s", name, e)
                self._health.record_result(name, success=False, error=str(e))
                self._update_stats(
                    name,
                    success=False,
                    empty=False,
                    fallback=False,
                    duration_ms=elapsed * 1000,
                    error_type=type(e).__name__,
                )

        # No provider returned valid data
        if last_empty and self.policy in (
            EmptyDataPolicy.BEST_EFFORT,
            EmptyDataPolicy.RELAXED,
        ):
            is_fallback = len(sources_tried) > 1 or last_source == "__cache__"
            self._update_stats(
                last_source, success=True, empty=True, fallback=is_fallback
            )
            return ExecutionResult(
                success=True,
                data=last_result,
                source=last_source,
                error="all_providers_returned_empty"
                if self.policy == EmptyDataPolicy.RELAXED
                else None,
                attempts=len(sources_tried),
                error_details=error_details,
                is_empty=True,
                is_fallback=is_fallback,
                sources_tried=sources_tried,
            )

        self._stats["failures"] += 1
        error_msg = (
            "all_providers_failed" if not last_empty else "all_providers_returned_empty"
        )
        return ExecutionResult(
            success=False,
            data=None,
            source=None,
            error=error_msg,
            attempts=len(sources_tried),
            error_details=error_details,
            is_empty=last_empty,
            is_fallback=False,
            sources_tried=sources_tried,
        )

    def _validate_result(self, data: Any) -> bool:
        if not self.required_columns and not self.min_rows:
            return data is not None
        if not isinstance(data, pd.DataFrame):
            return False
        if len(data) < self.min_rows:
            return False
        for col in self.required_columns:
            if col not in data.columns:
                return False
        return True

    def _update_stats(
        self,
        source: str,
        success: bool,
        empty: bool,
        fallback: bool,
        duration_ms: float = 0.0,
        error_type: Optional[str] = None,
    ) -> None:
        if success:
            self._stats["successes"] += 1
        if empty:
            self._stats["empty_results"] += 1
        if fallback:
            self._stats["fallbacks"] += 1

        if source:
            if source not in self._stats["source_stats"]:
                self._stats["source_stats"][source] = {
                    "successes": 0,
                    "failures": 0,
                    "empty": 0,
                }
            if success:
                self._stats["source_stats"][source]["successes"] += 1
            else:
                self._stats["source_stats"][source]["failures"] += 1
            if empty:
                self._stats["source_stats"][source]["empty"] += 1

        if self._stats_collector is not None:
            self._stats_collector.record_request(
                source,
                duration_ms,
                success,
                error_type=error_type,
            )

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    @property
    def health(self) -> SourceHealthMonitor:
        return self._health


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


def create_simple_router(
    callables: Dict[str, Callable],
    required_columns: Optional[List[str]] = None,
    min_rows: int = 0,
    policy: EmptyDataPolicy = EmptyDataPolicy.STRICT,
    stats_collector=None,
) -> MultiSourceRouter:
    """Create a ``MultiSourceRouter`` from a dict of ``{name: callable}``."""
    providers = [(name, func) for name, func in callables.items()]
    return MultiSourceRouter(
        providers=providers,
        required_columns=required_columns,
        min_rows=min_rows,
        policy=policy,
        stats_collector=stats_collector,
    )
