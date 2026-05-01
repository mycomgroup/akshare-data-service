"""TickFlow adapter for the ingestion layer.

Inline rewrite of ``analysis_v2.data.tickflow_adapter``.
TickFlow provides A-share, futures, US/HK stock data via SDK.
Requires: pip install tickflow
Optional dependency — adapter degrades gracefully if not installed.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from akshare_data.ingestion.base import DataSource

logger = logging.getLogger(__name__)

# Optional import — gracefully degrade
try:
    from tickflow import TickFlow

    _TICKFLOW_AVAILABLE = True
except ImportError:
    _TICKFLOW_AVAILABLE = False
    TickFlow = None  # type: ignore


class TickFlowAdapter(DataSource):
    """TickFlow data source adapter."""

    name = "tickflow"
    source_type = "real"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._tf = None
        self._available = False
        if _TICKFLOW_AVAILABLE:
            try:
                if api_key:
                    self._tf = TickFlow(api_key=api_key)
                else:
                    self._tf = TickFlow.free()
                self._available = True
            except Exception as e:
                logger.warning("TickFlow init failed: %s", e)
        else:
            logger.debug("tickflow package not installed")

    def is_configured(self) -> bool:
        return self._available

    def _require_available(self):
        if not self._available:
            raise RuntimeError(
                "TickFlow SDK is not installed or unavailable. Run: pip install tickflow"
            )

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if "." in symbol:
            return symbol.split(".")[0]
        return symbol

    @staticmethod
    def _to_tickflow_symbol(symbol: str) -> str:
        if "." in symbol:
            parts = symbol.split(".")
            code = parts[0]
            suffix = parts[1].upper()
            suffix_map = {"XSHE": "SZ", "XSHG": "SH", "SH": "SH", "SZ": "SZ", "BJ": "BJ"}
            return f"{code}.{suffix_map.get(suffix, suffix)}"
        code = symbol
        if code.startswith("399"):
            return f"{code}.SZ"
        elif code.startswith("6"):
            return f"{code}.SH"
        elif code.startswith("0") or code.startswith("3"):
            return f"{code}.SZ"
        elif code.startswith("8") or code.startswith("4") or code.startswith("9"):
            return f"{code}.BJ"
        return f"{code}.SZ"

    def _set_datetime_index(self, df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.set_index(date_col)
        df.index = pd.DatetimeIndex(df.index)
        return df.sort_index()

    @staticmethod
    def _to_numeric_cols(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    @staticmethod
    def _adjust_to_tickflow(adjust: str) -> str:
        return {"qfq": "forward", "hfq": "backward", "none": "none"}.get(adjust, "forward")

    # -- DataSource abstract methods ---------------------------------------

    def get_daily_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, date, datetime]] = None,
        end_date: Optional[Union[str, date, datetime]] = None,
        adjust: str = "qfq",
        **kwargs,
    ) -> pd.DataFrame:
        self._require_available()
        try:
            tf_symbol = self._to_tickflow_symbol(symbol)
            tf_adjust = self._adjust_to_tickflow(adjust)
            count = kwargs.get("count")

            if count is not None and start_date is None and end_date is None:
                df = self._tf.klines.get(
                    tf_symbol, period="1d", count=count, adjust=tf_adjust, as_dataframe=True
                )
            else:
                call_kwargs = {"period": "1d", "adjust": tf_adjust, "as_dataframe": True}
                if start_date:
                    call_kwargs["start_time"] = int(pd.Timestamp(start_date).timestamp() * 1000)
                if end_date:
                    call_kwargs["end_time"] = int(pd.Timestamp(end_date).timestamp() * 1000)
                if count is not None:
                    call_kwargs["count"] = count
                df = self._tf.klines.get(tf_symbol, **call_kwargs)

            if df is None or df.empty:
                return pd.DataFrame()

            col_map = {
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "amount": "amount",
                "trade_date": "date",
                "timestamp": "timestamp",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "date" not in df.columns and "trade_date" in df.columns:
                df["date"] = df["trade_date"]
            if "date" not in df.columns and "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            if "date" not in df.columns:
                return pd.DataFrame()

            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(df, ["open", "high", "low", "close", "volume", "amount"])
            return df
        except Exception as e:
            logger.error("get_daily_data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_index_components(
        self, index_code: str, include_weights: bool = True, **kwargs
    ) -> pd.DataFrame:
        logger.warning("TickFlow does not support index components")
        return pd.DataFrame()

    def get_trading_days(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> List[str]:
        logger.warning("TickFlow does not support trading calendar")
        return []

    def get_securities_list(
        self,
        security_type: str = "stock",
        date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        logger.warning("TickFlow does not support securities list")
        return pd.DataFrame()

    def get_security_info(self, symbol: str, **kwargs) -> Dict[str, Any]:
        return {"code": symbol, "type": "unknown", "display_name": None}

    def get_minute_data(
        self,
        symbol: str,
        freq: str = "1min",
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._require_available()
        try:
            tf_symbol = self._to_tickflow_symbol(symbol)
            period = freq.replace("min", "") + "min"
            call_kwargs = {"period": period, "adjust": "none", "as_dataframe": True}
            if start_date:
                call_kwargs["start_time"] = int(pd.Timestamp(start_date).timestamp() * 1000)
            if end_date:
                call_kwargs["end_time"] = int(pd.Timestamp(end_date).timestamp() * 1000)
            df = self._tf.klines.get(tf_symbol, **call_kwargs)
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {"open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume", "amount": "amount", "trade_date": "date"}
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "date" not in df.columns and "trade_date" in df.columns:
                df["date"] = df["trade_date"]
            if "date" in df.columns:
                df = self._set_datetime_index(df, "date")
                df = self._to_numeric_cols(df, ["open", "high", "low", "close", "volume", "amount"])
            return df
        except Exception as e:
            logger.error("get_minute_data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_money_flow(
        self,
        symbol: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        logger.warning("TickFlow does not support money flow")
        return pd.DataFrame()

    def get_north_money_flow(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        logger.warning("TickFlow does not support north money flow")
        return pd.DataFrame()

    def get_industry_stocks(
        self, industry_code: str, level: int = 1, **kwargs
    ) -> List[str]:
        logger.warning("TickFlow does not support industry stocks")
        return []

    def get_industry_mapping(self, symbol: str, level: int = 1, **kwargs) -> str:
        logger.warning("TickFlow does not support industry mapping")
        return ""

    # -- Health & info ------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ok" if self._available else "degraded",
            "tickflow_available": self._available,
        }

    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.source_type,
            "description": "TickFlow SDK data source adapter",
            "requires_auth": True,
            "tickflow_available": self._available,
        }
