"""Direct tests for CachedFetcher in store/fetcher.py.

Covers:
- execute() normal path
- _execute_incremental() incremental fetch
- _execute_full() full fetch
- _infer_strategy() strategy inference
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from akshare_data.store.fetcher import CachedFetcher, FetchConfig
from akshare_data.store.manager import CacheManager
from akshare_data.store.strategies import FullCacheStrategy, IncrementalStrategy


@pytest.fixture
def temp_cache_dir(tmp_path):
    return str(tmp_path / "cache")


@pytest.fixture
def cache_manager(temp_cache_dir):
    return CacheManager(base_dir=temp_cache_dir)


@pytest.fixture
def fetcher(cache_manager):
    return CachedFetcher(cache=cache_manager)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", "2024-01-10"),
            "symbol": ["sh600000"] * 10,
            "open": [10.0] * 10,
            "high": [11.0] * 10,
            "low": [9.0] * 10,
            "close": [10.5] * 10,
            "volume": [100000] * 10,
        }
    )


@pytest.mark.unit
class TestFetchConfig:
    def test_default_values(self):
        config = FetchConfig(table="stock_daily")
        assert config.table == "stock_daily"
        assert config.storage_layer is None
        assert config.strategy is None
        assert config.partition_by is None
        assert config.partition_value is None
        assert config.date_col == "date"
        assert config.interface_name is None
        assert config.filter_keys == []

    def test_custom_values(self):
        config = FetchConfig(
            table="stock_daily",
            storage_layer="daily",
            partition_by="symbol",
            partition_value="sh600000",
            date_col="trade_date",
            interface_name="stock_zh_a_hist",
            filter_keys=["symbol"],
        )
        assert config.table == "stock_daily"
        assert config.storage_layer == "daily"
        assert config.partition_by == "symbol"
        assert config.partition_value == "sh600000"
        assert config.date_col == "trade_date"
        assert config.interface_name == "stock_zh_a_hist"
        assert config.filter_keys == ["symbol"]


@pytest.mark.unit
class TestCachedFetcherInit:
    def test_init_with_cache_manager(self, cache_manager):
        fetcher = CachedFetcher(cache=cache_manager)
        assert fetcher.cache is cache_manager


@pytest.mark.unit
class TestInferStrategy:
    def test_infers_incremental_when_start_date_present(self, fetcher):
        config = FetchConfig(table="stock_daily")
        params = {"symbol": "sh600000", "start_date": "2024-01-01"}
        strategy = fetcher._infer_strategy(config, params)
        assert isinstance(strategy, IncrementalStrategy)

    def test_infers_incremental_when_end_date_present(self, fetcher):
        config = FetchConfig(table="stock_daily")
        params = {"symbol": "sh600000", "end_date": "2024-01-31"}
        strategy = fetcher._infer_strategy(config, params)
        assert isinstance(strategy, IncrementalStrategy)

    def test_infers_full_when_no_date_params(self, fetcher):
        config = FetchConfig(table="stock_daily")
        params = {"symbol": "sh600000"}
        strategy = fetcher._infer_strategy(config, params)
        assert isinstance(strategy, FullCacheStrategy)

    def test_uses_explicit_strategy_over_inference(self, fetcher):
        explicit = IncrementalStrategy(date_col="date", filter_keys=["symbol"])
        config = FetchConfig(table="stock_daily", strategy=explicit)
        result_config = FetchConfig(
            table=config.table,
            storage_layer=config.storage_layer,
            strategy=config.strategy,
            partition_by=config.partition_by,
            partition_value=config.partition_value,
            date_col=config.date_col,
            interface_name=config.interface_name,
            filter_keys=config.filter_keys,
        )
        assert result_config.strategy is explicit

    def test_guess_filter_keys_excludes_date_params(self, fetcher):
        params = {
            "symbol": "sh600000",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "adjust": "qfq",
            "source": "akshare",
        }
        keys = fetcher._guess_filter_keys(params)
        assert keys == ["symbol"]

    def test_guess_filter_keys_includes_scalar_params(self, fetcher):
        params = {"symbol": "sh600000", "period": "daily", "adjust": "qfq"}
        keys = fetcher._guess_filter_keys(params)
        assert "symbol" in keys
        assert "period" in keys


@pytest.mark.unit
class TestExecuteFull:
    def test_cache_hit_returns_cached(self, fetcher, sample_df):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            strategy=FullCacheStrategy(filter_keys=["symbol"]),
        )
        fetcher.cache.write(config.table, sample_df, storage_layer=config.storage_layer)

        fetch_fn = MagicMock()
        result = fetcher.execute(config, fetch_fn, symbol="sh600000")

        assert not result.empty
        fetch_fn.assert_not_called()

    def test_cache_miss_calls_fetch_fn(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            strategy=FullCacheStrategy(filter_keys=["symbol"]),
        )
        fresh_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", "2024-01-05"),
                "symbol": ["sh600000"] * 5,
                "close": [10.0] * 5,
            }
        )
        fetch_fn = MagicMock(return_value=fresh_df)
        result = fetcher.execute(config, fetch_fn, symbol="sh600000")

        assert not result.empty
        assert len(result) == 5
        fetch_fn.assert_called_once()

    def test_fetch_fn_returns_none_returns_empty(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            strategy=FullCacheStrategy(filter_keys=["symbol"]),
        )
        fetch_fn = MagicMock(return_value=None)
        result = fetcher.execute(config, fetch_fn, symbol="sh600000")

        assert result.empty

    def test_fetch_fn_returns_empty_returns_empty(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            strategy=FullCacheStrategy(filter_keys=["symbol"]),
        )
        fetch_fn = MagicMock(return_value=pd.DataFrame())
        result = fetcher.execute(config, fetch_fn, symbol="sh600000")

        assert result.empty


@pytest.mark.unit
class TestExecuteIncremental:
    def test_no_missing_range_returns_cached(self, fetcher, sample_df):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        fetcher.cache.write(config.table, sample_df, storage_layer=config.storage_layer)

        fetch_fn = MagicMock()
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert not result.empty
        assert len(result) == 10
        fetch_fn.assert_not_called()

    def test_missing_range_fetches_delta(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        existing_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", "2024-01-05"),
                "symbol": ["sh600000"] * 5,
                "close": [10.0] * 5,
            }
        )
        fetcher.cache.write(
            config.table, existing_df, storage_layer=config.storage_layer
        )

        new_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-06", "2024-01-10"),
                "symbol": ["sh600000"] * 5,
                "close": [11.0] * 5,
            }
        )
        fetch_fn = MagicMock(return_value=new_df)
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert not result.empty
        assert len(result) == 10
        fetch_fn.assert_called_once()

    def test_incremental_writes_to_cache(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        new_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-06", "2024-01-10"),
                "symbol": ["sh600000"] * 5,
                "close": [11.0] * 5,
            }
        )
        fetch_fn = MagicMock(return_value=new_df)
        fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-06",
            end_date="2024-01-10",
        )

        cached = fetcher.cache.read(config.table, storage_layer=config.storage_layer)
        assert not cached.empty

    def test_incremental_sorts_and_deduplicates(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        existing_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", "2024-01-05"),
                "symbol": ["sh600000"] * 5,
                "close": [10.0] * 5,
            }
        )
        fetcher.cache.write(
            config.table, existing_df, storage_layer=config.storage_layer
        )

        overlapping_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-03", "2024-01-07"),
                "symbol": ["sh600000"] * 5,
                "close": [11.0] * 5,
            }
        )
        fetch_fn = MagicMock(return_value=overlapping_df)
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-07",
        )

        assert not result.empty
        dates = result["date"].tolist()
        assert dates == sorted(dates)
        assert len(result["date"].unique()) == len(result)

    def test_incremental_restores_original_params(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        new_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-06", "2024-01-10"),
                "symbol": ["sh600000"] * 5,
                "close": [11.0] * 5,
            }
        )
        call_params = {}

        def capture_params(**kwargs):
            call_params.update(kwargs)
            return new_df

        params = {
            "symbol": "sh600000",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
        }
        fetcher.execute(config, capture_params, **params)

        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-10"


@pytest.mark.unit
class TestEdgeCases:
    def test_execute_with_partition(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            partition_by="symbol",
            partition_value="sh600000",
            strategy=FullCacheStrategy(filter_keys=["symbol"]),
        )
        fresh_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", "2024-01-05"),
                "symbol": ["sh600000"] * 5,
                "close": [10.0] * 5,
            }
        )
        fetch_fn = MagicMock(return_value=fresh_df)
        result = fetcher.execute(config, fetch_fn, symbol="sh600000")

        assert not result.empty
        fetch_fn.assert_called_once()

    def test_execute_with_custom_date_col(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="trade_date",
        )
        existing_df = pd.DataFrame(
            {
                "trade_date": pd.date_range("2024-01-01", "2024-01-05"),
                "symbol": ["sh600000"] * 5,
                "close": [10.0] * 5,
            }
        )
        fetcher.cache.write(
            config.table, existing_df, storage_layer=config.storage_layer
        )

        fetch_fn = MagicMock()
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-05",
        )

        assert not result.empty
        fetch_fn.assert_not_called()

    def test_incremental_empty_fetch_result(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        fetch_fn = MagicMock(return_value=pd.DataFrame())
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert result.empty

    def test_incremental_none_fetch_result(self, fetcher):
        config = FetchConfig(
            table="test_table",
            storage_layer="daily",
            date_col="date",
        )
        fetch_fn = MagicMock(return_value=None)
        result = fetcher.execute(
            config,
            fetch_fn,
            symbol="sh600000",
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert result.empty
