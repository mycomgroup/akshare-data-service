"""BaoStock adapter for the ingestion layer.

Inline rewrite of ``analysis_v2.data.baostock_adapter``.
BaoStock requires login; auto-login on first use.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from akshare_data.ingestion.base import DataSource

logger = logging.getLogger(__name__)


def _bs_result_to_df(result) -> pd.DataFrame:
    data_list = []
    while result.error_code == "0" and result.next():
        data_list.append(result.get_row_data())
    if not data_list:
        return pd.DataFrame()
    return pd.DataFrame(data_list, columns=result.fields)


class BaoStockAdapter(DataSource):
    """BaoStock data source adapter."""

    name = "baostock"
    source_type = "real"

    def __init__(self):
        self._bs = None
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            try:
                import baostock as bs

                self._bs = bs
                bs.login()
                self._connected = True
            except ImportError:
                raise RuntimeError(
                    "baostock is not installed. Run: pip install baostock"
                )
            except Exception as e:
                raise RuntimeError(f"baostock login failed: {e}")

    def is_configured(self) -> bool:
        try:
            import baostock  # noqa: F401

            return True
        except ImportError:
            return False

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        code = symbol
        if "." in code:
            code = code.split(".")[0]
        if code.startswith("6"):
            return f"sh.{code}"
        elif code.startswith("0") or code.startswith("3"):
            return f"sz.{code}"
        return code

    @staticmethod
    def _normalize_index_symbol(symbol: str) -> str:
        code = symbol
        if "." in code:
            code = code.split(".")[0]
        return f"sh.{code}"

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
        self._ensure_connected()
        try:
            bs_symbol = self._normalize_symbol(symbol)
            adjust_map = {"qfq": "2", "hfq": "1", "none": "3"}
            adj = adjust_map.get(adjust, "2")
            fields = "date,open,high,low,close,volume,amount,turn"

            count = kwargs.get("count")
            if count is not None and start_date is None:
                end = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
                estimated_days = int(count * 1.5) + 30
                start_est = pd.Timestamp(end) - pd.Timedelta(days=estimated_days)
                start_date = start_est.strftime("%Y-%m-%d")

            start = start_date or "1990-01-01"
            end = end_date or "2050-01-01"

            result = self._bs.query_history_k_data_plus(
                bs_symbol, fields, start_date=str(start), end_date=str(end), frequency="d", adjustflag=adj
            )
            df = _bs_result_to_df(result)
            if df.empty:
                return pd.DataFrame()
            df = self._set_datetime_index(df, "date")
            df = df.rename(columns={"turn": "turnover_rate"})
            df = self._to_numeric_cols(
                df, ["open", "high", "low", "close", "volume", "amount", "turnover_rate"]
            )
            if count is not None:
                df = df.tail(count)
            return df
        except Exception as e:
            logger.error("get_daily_data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_index_components(
        self, index_code: str, include_weights: bool = True, **kwargs
    ) -> pd.DataFrame:
        self._ensure_connected()
        try:
            result = self._bs.query_sz50_stocks() if "000016" in index_code else self._bs.query_hs300_stocks()
            df = _bs_result_to_df(result)
            if df.empty:
                return pd.DataFrame()
            result = pd.DataFrame()
            result["index_code"] = index_code
            if "code" in df.columns:
                result["code"] = df["code"].astype(str).str.replace(r"^(sh|sz)\.", "", regex=True).str.zfill(6)
            if "code_name" in df.columns:
                result["stock_name"] = df["code_name"]
            return result
        except Exception as e:
            logger.error("get_index_components for %s: %s", index_code, e)
            return pd.DataFrame()

    def get_trading_days(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> List[str]:
        self._ensure_connected()
        try:
            result = self._bs.query_trade_dates()
            df = _bs_result_to_df(result)
            if df.empty:
                return []
            if "calendar_date" in df.columns:
                dates = pd.to_datetime(df["calendar_date"], errors="coerce").dropna().sort_values()
            else:
                return []
            if start_date:
                dates = dates[dates >= pd.Timestamp(start_date)]
            if end_date:
                dates = dates[dates <= pd.Timestamp(end_date)]
            return [d.strftime("%Y-%m-%d") for d in dates]
        except Exception as e:
            logger.error("get_trading_days: %s", e)
            return []

    def get_securities_list(
        self,
        security_type: str = "stock",
        date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_connected()
        try:
            if security_type == "stock":
                result = self._bs.query_all_stock(day=date or pd.Timestamp.today().strftime("%Y-%m-%d"))
            else:
                return pd.DataFrame()
            df = _bs_result_to_df(result)
            if df.empty:
                return pd.DataFrame()
            df["type"] = security_type
            return df
        except Exception as e:
            logger.error("get_securities_list for %s: %s", security_type, e)
            return pd.DataFrame()

    def get_security_info(self, symbol: str, **kwargs) -> Dict[str, Any]:
        self._ensure_connected()
        try:
            bs_symbol = self._normalize_symbol(symbol)
            result = self._bs.query_stock_basic(code=bs_symbol)
            df = _bs_result_to_df(result)
            if df.empty:
                return {"code": symbol, "type": "unknown"}
            info = {"code": symbol}
            if "code_name" in df.columns:
                info["display_name"] = str(df["code_name"].iloc[0])
            if "ipoDate" in df.columns:
                info["start_date"] = str(df["ipoDate"].iloc[0])
            if "outDate" in df.columns:
                info["end_date"] = str(df["outDate"].iloc[0]) if df["outDate"].iloc[0] else None
            info["type"] = "stock"
            return info
        except Exception as e:
            logger.error("get_security_info for %s: %s", symbol, e)
            return {"code": symbol, "type": "unknown"}

    def get_minute_data(
        self,
        symbol: str,
        freq: str = "1min",
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_connected()
        try:
            bs_symbol = self._normalize_symbol(symbol)
            period = freq.replace("min", "")
            fields = "date,open,high,low,close,volume,amount"
            start = start_date or pd.Timestamp.today().strftime("%Y-%m-%d")
            end = end_date or start
            result = self._bs.query_history_k_data_plus(
                bs_symbol, fields, start_date=str(start), end_date=str(end), frequency=period, adjustflag="3"
            )
            df = _bs_result_to_df(result)
            if df.empty:
                return pd.DataFrame()
            df = self._set_datetime_index(df, "date")
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
        logger.warning("BaoStock does not support money flow data")
        return pd.DataFrame()

    def get_north_money_flow(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        logger.warning("BaoStock does not support north money flow data")
        return pd.DataFrame()

    def get_industry_stocks(
        self, industry_code: str, level: int = 1, **kwargs
    ) -> List[str]:
        logger.warning("BaoStock does not support industry stocks")
        return []

    def get_industry_mapping(self, symbol: str, level: int = 1, **kwargs) -> str:
        logger.warning("BaoStock does not support industry mapping")
        return ""

    # -- Additional methods ------------------------------------------------

    def get_valuation(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        self._ensure_connected()
        try:
            bs_symbol = self._normalize_symbol(symbol)
            fields = "date,peTTM,psTTM"
            start = start_date or (pd.Timestamp.today() - pd.Timedelta(days=365 * 3)).strftime("%Y-%m-%d")
            end = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
            result = self._bs.query_history_k_data_plus(
                bs_symbol, fields, start_date=str(start), end_date=str(end), frequency="d", adjustflag="2"
            )
            df = _bs_result_to_df(result)
            if df.empty:
                return pd.DataFrame()
            df = self._set_datetime_index(df, "date")
            df = df.rename(columns={"peTTM": "pe_ratio", "psTTM": "ps_ratio"})
            df = self._to_numeric_cols(df, ["pe_ratio", "ps_ratio"])
            df["pb_ratio"] = None
            df["pcf_ratio"] = None
            return df
        except Exception as e:
            logger.error("get_valuation for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_stock_valuation(self, symbol: str) -> pd.DataFrame:
        return self.get_valuation(symbol)

    def get_finance_indicator(
        self,
        symbol: str,
        fields: Optional[List[str]] = None,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        self._ensure_connected()
        try:
            bs_symbol = self._normalize_symbol(symbol)
            now = pd.Timestamp.today()
            current_q = (now.month - 1) // 3 + 1
            years, quarters = [], []
            for i in range(8):
                q = current_q - i
                y = now.year
                while q <= 0:
                    q += 4
                    y -= 1
                quarters.append(q)
                years.append(y)

            all_data = []
            for y, q in zip(years, quarters):
                r = self._bs.query_profit_data(code=bs_symbol, year=y, quarter=q)
                df = _bs_result_to_df(r)
                if not df.empty:
                    all_data.append(df)

            if not all_data:
                return pd.DataFrame()

            df = pd.concat(all_data, ignore_index=True)
            if "statDate" in df.columns:
                df["date"] = pd.to_datetime(df["statDate"], errors="coerce")
                df = df.set_index("date")
                df.index = pd.DatetimeIndex(df.index)
            df = df.rename(columns={"roeAvg": "roe", "npMargin": "net_profit_margin", "gpMargin": "gross_profit_margin"})
            return df.sort_index()
        except Exception as e:
            logger.error("get_finance_indicator for %s: %s", symbol, e)
            return pd.DataFrame()

    def health_check(self) -> Dict[str, Any]:
        try:
            if not self.is_configured():
                return {"status": "error", "message": "baostock not installed"}
            self._ensure_connected()
            return {"status": "ok", "message": "BaoStock connected"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.source_type,
            "description": "BaoStock data source adapter",
            "requires_auth": False,
        }
