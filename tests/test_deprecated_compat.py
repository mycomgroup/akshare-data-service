"""Tests for deprecated compatibility shell modules.

Verifies that importing deprecated modules raises DeprecationWarning
with correct messages pointing to the new module locations.
"""

import subprocess
import sys
import warnings

import pytest


def _check_deprecation_warning(module_path: str, expected_msg: str):
    """Run import in subprocess to avoid module caching issues."""
    code = f"""
import warnings
warnings.simplefilter("always", DeprecationWarning)
import {module_path}
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert expected_msg in result.stderr, (
        f"Expected '{expected_msg}' in stderr, got: {result.stderr}"
    )


@pytest.mark.unit
class TestDeprecatedStats:
    def test_import_raises_deprecation_warning(self):
        _check_deprecation_warning(
            "akshare_data.core.stats",
            "akshare_data.core.stats is deprecated",
        )

    def test_re_exports_work(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from akshare_data.core.stats import (
                RequestStats,
                CacheStats,
                StatsCollector,
            )

            assert RequestStats is not None
            assert CacheStats is not None
            assert StatsCollector is not None


@pytest.mark.unit
class TestDeprecatedConfigDir:
    def test_import_raises_deprecation_warning(self):
        _check_deprecation_warning(
            "akshare_data.core.config_dir",
            "akshare_data.core.config_dir is deprecated",
        )

    def test_re_exports_work(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from akshare_data.core.config_dir import get_config_dir, get_project_root

            assert callable(get_config_dir)
            assert callable(get_project_root)


@pytest.mark.unit
class TestDeprecatedConfigCache:
    def test_import_raises_deprecation_warning(self):
        _check_deprecation_warning(
            "akshare_data.core.config_cache",
            "akshare_data.core.config_cache is deprecated",
        )

    def test_re_exports_work(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from akshare_data.core.config_cache import ConfigCache

            assert ConfigCache is not None


@pytest.mark.unit
class TestDeprecatedErrors:
    def test_import_raises_deprecation_warning(self):
        _check_deprecation_warning(
            "akshare_data.core.errors",
            "akshare_data.core.errors is deprecated",
        )

    def test_re_exports_work(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from akshare_data.core.errors import (
                ErrorCode,
                DataAccessException,
                DataSourceError,
            )

            assert ErrorCode is not None
            assert DataSourceError is not None
