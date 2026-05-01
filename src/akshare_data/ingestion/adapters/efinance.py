"""EFinance adapter for the ingestion layer.

Inline rewrite of ``analysis_v2.data.efinance_adapter``.
EFinance provides fast real-time quotes and historical data.
Requires: pip install efinance
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from akshare_data.ingestion.base import DataSource

logger = logging.getLogger(__name__)


class EFinanceAdapter(DataSource):
    """EFinance data source adapter."""

    name = "efinance"
    source_type = "real"

    def __init__(self):
        self._efinance = None
        self._available = True

    def _ensure_efinance(self):
        if self._efinance is not None:
            return
        try:
            import efinance as ef

            self._efinance = ef
        except ImportError:
            raise RuntimeError("efinance is not installed. Run: pip install efinance")

    def is_configured(self) -> bool:
        try:
            import efinance  # noqa: F401

            return True
        except ImportError:
            return False

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        code = symbol
        if "." in code:
            code = code.split(".")[0]
        return code

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

    # -- DataSource abstract methods ---------------------------------------

    def get_daily_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, date, datetime]] = None,
        end_date: Optional[Union[str, date, datetime]] = None,
        adjust: str = "qfq",
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_efinance()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            qfq_map = {"qfq": 1, "hfq": 2, "none": 0}
            df = self._efinance.stock.get_quote_history(
                ak_symbol, klt=101, klt_type=qfq_map.get(adjust, 1)
            )
            if df is None or df.empty:
                return pd.DataFrame()
            drop_cols = [c for c in ["股票名称", "股票代码"] if c in df.columns]
            df = df.drop(columns=drop_cols)
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "换手率": "turnover_rate",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(
                df,
                ["open", "high", "low", "close", "volume", "amount", "amplitude", "change_pct", "change", "turnover_rate"],
            )
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            if kwargs.get("count") is not None:
                df = df.tail(kwargs["count"])
            return df
        except Exception as e:
            logger.error("get_daily_data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_index_components(
        self, index_code: str, include_weights: bool = True, **kwargs
    ) -> pd.DataFrame:
        logger.warning("EFinance does not support index components")
        return pd.DataFrame()

    def get_trading_days(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> List[str]:
        logger.warning("EFinance does not support trading calendar")
        return []

    def get_securities_list(
        self,
        security_type: str = "stock",
        date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_efinance()
        try:
            if security_type in ("stock", "etf"):
                df = self._efinance.stock.get_realtime_quotes()
            else:
                return pd.DataFrame()
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {"股票代码": "code", "股票名称": "display_name"}
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            df["type"] = security_type
            return df[[c for c in ["code", "display_name", "type"] if c in df.columns]]
        except Exception as e:
            logger.error("get_securities_list for %s: %s", security_type, e)
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
        self._ensure_efinance()
        try:
            code = self._normalize_symbol(symbol)
            klt_map = {"1min": 1, "5min": 5, "15min": 15, "30min": 30, "60min": 60}
            klt = klt_map.get(freq, 5)
            df = self._efinance.stock.get_quote_history(code, klt=klt)
            if df is None or df.empty:
                return pd.DataFrame()
            drop_cols = [c for c in ["股票名称", "股票代码"] if c in df.columns]
            df = df.drop(columns=drop_cols)
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "date" in df.columns and start_date is not None:
                date_ts = pd.Timestamp(start_date)
                df = df[df["date"].astype(str).str.startswith(date_ts.strftime("%Y-%m-%d"))]
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
        logger.warning("EFinance does not support money flow")
        return pd.DataFrame()

    def get_north_money_flow(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        logger.warning("EFinance does not support north money flow")
        return pd.DataFrame()

    def get_industry_stocks(
        self, industry_code: str, level: int = 1, **kwargs
    ) -> List[str]:
        logger.warning("EFinance does not support industry stocks")
        return []

    def get_industry_mapping(self, symbol: str, level: int = 1, **kwargs) -> str:
        logger.warning("EFinance does not support industry mapping")
        return ""

    # -- Additional methods ------------------------------------------------

    def get_spot_em(self) -> pd.DataFrame:
        self._ensure_efinance()
        try:
            df = self._efinance.stock.get_realtime_quotes()
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "股票代码": "symbol",
                "股票名称": "name",
                "最新价": "close",
                "涨跌幅": "change_pct",
                "成交量": "volume",
                "成交额": "amount",
                "总市值": "market_cap",
                "动态市盈率": "pe_ratio",
                "换手率": "turnover_rate",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            keep_cols = ["symbol", "name", "close", "change_pct", "volume", "amount", "market_cap", "pe_ratio", "turnover_rate"]
            df = df[[c for c in keep_cols if c in df.columns]]
            df = self._to_numeric_cols(df, ["close", "change_pct", "volume", "amount", "market_cap", "pe_ratio", "turnover_rate"])
            if "symbol" in df.columns:
                df = df.set_index("symbol")
            return df
        except Exception as e:
            logger.error("get_spot_em: %s", e)
            return pd.DataFrame()

    def get_index_daily(
        self,
        symbol: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_efinance()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            df = self._efinance.stock.get_quote_history(ak_symbol, klt=101, is_index=True)
            if df is None or df.empty:
                return pd.DataFrame()
            drop_cols = [c for c in ["股票名称", "股票代码"] if c in df.columns]
            df = df.drop(columns=drop_cols)
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "换手率": "turnover_rate",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(
                df,
                ["open", "high", "low", "close", "volume", "amount", "amplitude", "change_pct", "change", "turnover_rate"],
            )
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            return df
        except Exception as e:
            logger.error("get_index_daily for %s: %s", symbol, e)
            return pd.DataFrame()

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ok" if self.is_configured() else "degraded",
            "efinance_available": self.is_configured(),
        }

    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.source_type,
            "description": "EFinance data source adapter",
            "requires_auth": False,
        }
