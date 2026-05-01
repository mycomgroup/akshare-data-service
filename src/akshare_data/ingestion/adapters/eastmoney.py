"""EastMoney adapter for the ingestion layer.

Implements ``ingestion.base.DataSource`` using AKShare's EastMoney APIs.
Focus: trading events, sector concepts, fund flows, northbound data,
convertible bonds, etc.

This is an inline rewrite of ``analysis_v2.data.eastmoney_adapter``
for the ``akshare-data-service`` ingestion layer.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from akshare_data.ingestion.base import DataSource

logger = logging.getLogger(__name__)

_RETRIABLE = (ConnectionError, TimeoutError, OSError)


def _classify_error(e: Exception) -> str:
    if isinstance(e, _RETRIABLE):
        return "retryable"
    elif isinstance(e, (KeyError, ValueError, TypeError, IndexError)):
        return "api_error"
    return "unknown"


def _log_api_error(action: str, e: Exception, level: str = "error") -> None:
    et = _classify_error(e)
    if et == "retryable":
        logger.warning("%s failed (retryable, %s): %s", action, type(e).__name__, e)
    elif et == "api_error":
        logger.error("%s failed (api_error, %s): %s", action, type(e).__name__, e)
    else:
        (logger.error if level == "error" else logger.warning)(
            "%s failed (unknown, %s): %s", action, type(e).__name__, e
        )


class EastMoneyAdapter(DataSource):
    """EastMoney data source adapter (via AKShare)."""

    name = "eastmoney"
    source_type = "real"

    def __init__(self):
        self._available = True
        self._ak = None
        try:
            import akshare as ak

            self._ak = ak
        except ImportError:
            logger.warning("akshare not installed; EastMoney adapter unavailable")
            self._available = False

    def is_configured(self) -> bool:
        return self._available

    def _require_available(self):
        if not self._available:
            raise RuntimeError("akshare is not available")

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if "." in symbol:
            return symbol.split(".")[0]
        return symbol

    @staticmethod
    def _normalize_date(val: Optional[Union[str, date, datetime]]) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, (date, datetime)):
            return val.strftime("%Y-%m-%d")
        return str(val).replace("-", "")

    @staticmethod
    def _normalize_df_columns(df: pd.DataFrame, col_map: Dict[str, str]) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        return df

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

    def _estimate_start_date(self, count: int) -> Optional[str]:
        end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
        try:
            cal = self.get_trading_days(end_date=end_date)
            if len(cal) > 0:
                target = count * 2
                if len(cal) >= target:
                    return cal[-target]
                return cal[0]
        except Exception as e:
            logger.debug("_estimate_start_date: calendar check failed: %s", e)
        start_dt = pd.Timestamp(end_date) - pd.offsets.BDay(count * 2)
        return start_dt.strftime("%Y-%m-%d")

    # -- DataSource abstract methods ---------------------------------------

    def get_daily_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, date, datetime]] = None,
        end_date: Optional[Union[str, date, datetime]] = None,
        adjust: str = "qfq",
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV via EastMoney (AKShare ``stock_zh_a_hist``)."""
        self._require_available()
        try:
            count = kwargs.get("count")
            if count is not None and start_date is None and end_date is None:
                end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
                start_date = self._estimate_start_date(count)
            ak_symbol = self._normalize_symbol(symbol)
            adj = "" if adjust == "none" else adjust
            df = self._ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=self._normalize_date(start_date) or "19900101",
                end_date=self._normalize_date(end_date) or "20500101",
                adjust=adj,
            )
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "换手率": "turnover_rate",
            }
            df = self._normalize_df_columns(df, col_map)
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(
                df, ["open", "high", "low", "close", "volume", "amount", "turnover_rate"]
            )
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            if count is not None:
                df = df.tail(count)
            return df.sort_index()
        except Exception as e:
            _log_api_error(f"get_daily_data for {symbol}", e)
            return pd.DataFrame()

    def get_index_components(
        self, index_code: str, include_weights: bool = True, **kwargs
    ) -> pd.DataFrame:
        """Fetch index constituents via AKShare ``index_stock_cons``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(index_code)
            df = self._ak.index_stock_cons(symbol=ak_symbol)
            if df is None or df.empty:
                return pd.DataFrame()
            result = pd.DataFrame()
            result["index_code"] = index_code
            for col in df.columns:
                if "代码" in col or "code" in col.lower() or "symbol" in col.lower():
                    result["code"] = df[col].astype(str).str.zfill(6)
                    break
            if "code" not in result.columns and len(df.columns) > 0:
                result["code"] = df.iloc[:, 0].astype(str).str.zfill(6)
            if "name" in df.columns or "名称" in df.columns:
                name_col = "name" if "name" in df.columns else "名称"
                result["stock_name"] = df[name_col]
            if include_weights and "weight" in df.columns:
                result["weight"] = pd.to_numeric(df["weight"], errors="coerce")
            if "date" in df.columns:
                result["effective_date"] = pd.to_datetime(df["date"], errors="coerce")
            return result
        except Exception as e:
            _log_api_error(f"get_index_components for {index_code}", e)
            return pd.DataFrame()

    def get_trading_days(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> List[str]:
        """Fetch trading calendar via AKShare ``tool_trade_date_hist_sina``."""
        self._require_available()
        try:
            df = self._ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                return []
            date_col = None
            for col in df.columns:
                if "日期" in col or "date" in col.lower() or "trade" in col.lower():
                    date_col = col
                    break
            if date_col is None:
                date_col = df.columns[0]
            dates = pd.to_datetime(df[date_col]).sort_values()
            if start_date:
                dates = dates[dates >= pd.Timestamp(start_date)]
            if end_date:
                dates = dates[dates <= pd.Timestamp(end_date)]
            return [d.strftime("%Y-%m-%d") for d in dates]
        except Exception as e:
            _log_api_error("get_trading_days", e)
            return []

    def get_securities_list(
        self,
        security_type: str = "stock",
        date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch securities list (stocks/ETF/index) via EastMoney spot API."""
        self._require_available()
        try:
            if security_type in ("stock", "etf", "fund"):
                df = self._ak.stock_zh_a_spot()
            elif security_type == "index":
                df = self._ak.stock_zh_index_spot()
            else:
                df = self._ak.stock_zh_a_spot()
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "代码": "code",
                "名称": "display_name",
            }
            df = self._normalize_df_columns(df, col_map)
            if "code" not in df.columns and len(df.columns) > 0:
                df["code"] = df.iloc[:, 0]
            if "display_name" not in df.columns and len(df.columns) > 1:
                df["display_name"] = df.iloc[:, 1]
            df["type"] = security_type
            return df[[c for c in ["code", "display_name", "type"] if c in df.columns]]
        except Exception as e:
            _log_api_error(f"get_securities_list for {security_type}", e)
            return pd.DataFrame()

    def get_security_info(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch basic security info via AKShare ``stock_profile_cninfo``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            info_df = self._ak.stock_profile_cninfo(symbol=ak_symbol)
            if info_df is None or info_df.empty:
                return {"code": symbol, "type": "unknown"}
            info: Dict[str, Any] = {"code": symbol}
            for col in info_df.columns:
                value = info_df[col].iloc[0] if len(info_df) > 0 else None
                if value is None or pd.isna(value):
                    continue
                if "公司" in col and "名称" in col:
                    info["display_name"] = str(value)
                elif "行业" in col:
                    info["industry"] = str(value)
                elif "上市" in col and "日期" in col:
                    info["start_date"] = str(value)
            info.setdefault("display_name", None)
            info.setdefault("industry", None)
            info.setdefault("start_date", None)
            info.setdefault("end_date", None)
            info.setdefault("type", "stock")
            return info
        except Exception as e:
            _log_api_error(f"get_security_info for {symbol}", e)
            return {"code": symbol, "type": "unknown"}

    def get_minute_data(
        self,
        symbol: str,
        freq: str = "1min",
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch minute-level data via AKShare ``stock_zh_a_minute``."""
        self._require_available()
        try:
            code = self._normalize_symbol(symbol)
            prefix = "sh" if code.startswith("6") else "sz"
            tx_symbol = f"{prefix}{code}"
            period = freq.replace("min", "")
            df = self._ak.stock_zh_a_minute(symbol=tx_symbol, period=period, adjust="")
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "day": "date",
                "open": "open",
                "close": "close",
                "high": "high",
                "low": "low",
                "volume": "volume",
                "amount": "amount",
            }
            df = self._normalize_df_columns(df, col_map)
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(df, ["open", "high", "low", "close", "volume", "amount"])
            return df
        except Exception as e:
            _log_api_error(f"get_minute_data for {symbol}", e)
            return pd.DataFrame()

    def get_money_flow(
        self,
        symbol: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch money flow via AKShare ``stock_individual_fund_flow``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            market = "sh" if ak_symbol.startswith("6") else "sz"
            df = self._ak.stock_individual_fund_flow(stock=ak_symbol, market=market)
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "日期": "date",
                "主力净流入-净额": "main_net",
                "主力净流入-净占比": "main_net_ratio",
                "小单净流入-净额": "retail_net",
                "小单净流入-净占比": "retail_net_ratio",
                "中单净流入-净额": "medium_net",
                "中单净流入-净占比": "medium_net_ratio",
                "大单净流入-净额": "large_net",
                "大单净流入-净占比": "large_net_ratio",
                "超大单净流入-净额": "super_net",
                "超大单净流入-净占比": "super_net_ratio",
            }
            df = self._normalize_df_columns(df, col_map)
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(
                df,
                [
                    "main_net",
                    "main_net_ratio",
                    "retail_net",
                    "retail_net_ratio",
                    "medium_net",
                    "medium_net_ratio",
                    "large_net",
                    "large_net_ratio",
                    "super_net",
                    "super_net_ratio",
                ],
            )
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            return df
        except Exception as e:
            _log_api_error(f"get_money_flow for {symbol}", e)
            return pd.DataFrame()

    def get_north_money_flow(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch northbound money flow via AKShare ``stock_hsgt_hist_em``."""
        self._require_available()
        try:
            df = self._ak.stock_hsgt_hist_em(symbol="北向资金")
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "日期": "date",
                "当日净流入": "north_net",
                "当日成交净买额": "north_net",
                "当日买入额": "buy_amount",
                "买入成交额": "buy_amount",
                "当日卖出额": "sell_amount",
                "卖出成交额": "sell_amount",
            }
            df = self._normalize_df_columns(df, col_map)
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(df, ["north_net", "buy_amount", "sell_amount"])
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            return df
        except Exception as e:
            _log_api_error("get_north_money_flow", e)
            return pd.DataFrame()

    def get_industry_stocks(
        self, industry_code: str, level: int = 1, **kwargs
    ) -> List[str]:
        """Fetch industry constituent stocks via AKShare ``stock_board_industry_cons_em``."""
        self._require_available()
        try:
            df = self._ak.stock_board_industry_cons_em(symbol=industry_code)
            if df is None or df.empty:
                return []
            code_col = None
            for col in df.columns:
                if "代码" in col or "code" in col.lower():
                    code_col = col
                    break
            if code_col is None:
                return []
            return [str(c).zfill(6) for c in df[code_col].tolist() if pd.notna(c)]
        except Exception as e:
            _log_api_error(f"get_industry_stocks for {industry_code}", e)
            return []

    def get_industry_mapping(self, symbol: str, level: int = 1, **kwargs) -> str:
        """Fetch stock industry mapping via ``stock_profile_cninfo``."""
        self._require_available()
        try:
            info = self.get_security_info(symbol)
            return info.get("industry", "")
        except Exception as e:
            _log_api_error(f"get_industry_mapping for {symbol}", e)
            return ""

    # -- Additional methods (Mixin overrides) ------------------------------

    def get_call_auction(
        self, symbol: str, date: Optional[Union[str, date]] = None, **kwargs
    ) -> pd.DataFrame:
        """Fetch call auction (tick) data via AKShare ``stock_zh_a_tick_txjs``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            fmt_date = self._normalize_date(date) or pd.Timestamp.today().strftime("%Y%m%d")
            df = self._ak.stock_zh_a_tick_txjs(symbol=ak_symbol, trade_date=fmt_date)
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "时间": "time",
                "价格": "price",
                "成交量": "volume",
                "成交额": "amount",
                "买盘量": "bid_volume",
                "卖盘量": "ask_volume",
            }
            df = self._normalize_df_columns(df, col_map)
            if "time" in df.columns and date is not None:
                date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
                df["datetime"] = pd.to_datetime(date_str + " " + df["time"].astype(str))
                df = df.set_index("datetime")
                df.index = pd.DatetimeIndex(df.index)
            df = self._to_numeric_cols(df, ["price", "volume", "amount", "bid_volume", "ask_volume"])
            return df.sort_index()
        except Exception as e:
            _log_api_error(f"get_call_auction for {symbol}", e)
            return pd.DataFrame()

    def get_stock_valuation(self, symbol: str) -> pd.DataFrame:
        """Fetch stock valuation via AKShare ``stock_value_em``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            df = self._ak.stock_value_em(symbol=ak_symbol)
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "数据日期": "date",
                "总市值": "market_cap",
                "流通市值": "circulating_market_cap",
                "PE(TTM)": "pe_ratio",
                "市净率": "pb_ratio",
                "市销率": "ps_ratio",
                "市现率": "pcf_ratio",
            }
            df = self._normalize_df_columns(df, col_map)
            keep_cols = [c for c in col_map.values() if c in df.columns]
            if "date" not in keep_cols:
                return pd.DataFrame()
            df = df[keep_cols]
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(
                df, ["pe_ratio", "pb_ratio", "ps_ratio", "pcf_ratio", "market_cap", "circulating_market_cap"]
            )
            return df.sort_index()
        except Exception as e:
            _log_api_error(f"get_stock_valuation for {symbol}", e)
            return pd.DataFrame()

    def get_index_valuation(self, index_code: str) -> pd.DataFrame:
        """Fetch index PE/PB via AKShare ``stock_index_pe_lg`` / ``stock_index_pb_lg``."""
        self._require_available()
        try:
            norm_symbol = self._normalize_symbol(index_code)
            index_name_map = {
                "000300": "沪深300",
                "000016": "上证50",
                "000905": "中证500",
                "000852": "中证1000",
                "399006": "创业板指",
                "000001": "上证指数",
            }
            index_name = index_name_map.get(norm_symbol, norm_symbol)
            try:
                df_pe = self._ak.stock_index_pe_lg(symbol=index_name)
            except Exception as e:
                logger.warning("stock_index_pe_lg failed: %s, %s", index_name, e)
                df_pe = pd.DataFrame()
            try:
                df_pb = self._ak.stock_index_pb_lg(symbol=index_name)
            except Exception as e:
                logger.warning("stock_index_pb_lg failed: %s, %s", index_name, e)
                df_pb = pd.DataFrame()
            if df_pe.empty and df_pb.empty:
                return pd.DataFrame()
            result = pd.DataFrame()
            if not df_pe.empty:
                col_map_pe = {"日期": "date", "滚动市盈率": "pe"}
                df_pe = self._normalize_df_columns(df_pe, col_map_pe)
                if "date" in df_pe.columns and "pe" in df_pe.columns:
                    result = df_pe[["date", "pe"]].copy()
            if not df_pb.empty:
                col_map_pb = {"日期": "date", "市净率": "pb"}
                df_pb = self._normalize_df_columns(df_pb, col_map_pb)
                if "date" in df_pb.columns and "pb" in df_pb.columns:
                    df_pb = df_pb[["date", "pb"]].copy()
                    if result.empty:
                        result = df_pb
                    else:
                        result = result.merge(df_pb, on="date", how="outer")
            if result.empty:
                return pd.DataFrame()
            result = result.drop_duplicates(subset=["date"], keep="last")
            result = self._set_datetime_index(result, "date")
            result = self._to_numeric_cols(result, ["pe", "pb"])
            return result.sort_index()
        except Exception as e:
            _log_api_error(f"get_index_valuation for {index_code}", e)
            return pd.DataFrame()

    def get_dividend(self, symbol: str) -> pd.DataFrame:
        """Fetch dividend data via AKShare ``stock_history_dividend_detail``."""
        self._require_available()
        try:
            ak_symbol = self._normalize_symbol(symbol)
            df = self._ak.stock_history_dividend_detail(symbol=ak_symbol, indicator="分红")
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "除权除息日": "date",
                "分红日期": "date",
                "日期": "date",
                "派息": "cash_dividend",
                "每股派息": "cash_dividend",
                "现金股利": "cash_dividend",
                "送股": "stock_dividend",
                "送股比例": "stock_dividend",
                "转增": "stock_split",
                "转增比例": "stock_split",
            }
            df = self._normalize_df_columns(df, col_map)
            if "date" in df.columns:
                df["ex_date"] = df["date"]
            keep_cols = ["date", "ex_date", "cash_dividend", "stock_dividend", "stock_split"]
            keep_cols = [c for c in keep_cols if c in df.columns]
            if "date" not in keep_cols:
                return pd.DataFrame()
            df = df[keep_cols]
            df = df.dropna(subset=["date"])
            df = self._set_datetime_index(df, "date")
            df = df[~df.index.duplicated(keep="last")]
            df = self._to_numeric_cols(df, ["cash_dividend", "stock_dividend", "stock_split"])
            return df.sort_index()
        except Exception as e:
            _log_api_error(f"get_dividend for {symbol}", e)
            return pd.DataFrame()

    def get_spot_em(self) -> pd.DataFrame:
        """Fetch full market spot data via AKShare ``stock_zh_a_spot``."""
        self._require_available()
        try:
            df = self._ak.stock_zh_a_spot()
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "code": "symbol",
                "代码": "symbol",
                "name": "name",
                "名称": "name",
                "trade": "close",
                "最新价": "close",
                "pricechange": "change_pct",
                "涨跌幅": "change_pct",
                "volume": "volume",
                "成交量": "volume",
                "amount": "amount",
                "成交额": "amount",
                "mktcap": "market_cap",
                "总市值": "market_cap",
                "nmc": "circulating_market_cap",
                "流通市值": "circulating_market_cap",
                "pe": "pe_ratio",
                "市盈率-动态": "pe_ratio",
                "pb": "pb_ratio",
                "市净率": "pb_ratio",
                "turnoverratio": "turnover_rate",
                "换手率": "turnover_rate",
            }
            df = self._normalize_df_columns(df, col_map)
            df = self._to_numeric_cols(
                df, ["close", "change_pct", "volume", "amount", "market_cap", "pe_ratio", "pb_ratio", "turnover_rate"]
            )
            if "symbol" in df.columns:
                df = df.set_index("symbol")
            return df
        except Exception as e:
            _log_api_error("get_spot_em", e)
            return pd.DataFrame()

    def get_securities_code_name(self) -> pd.DataFrame:
        """Fetch A-share code-name mapping via AKShare ``stock_info_a_code_name``."""
        self._require_available()
        try:
            df = self._ak.stock_info_a_code_name()
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            _log_api_error("get_securities_code_name", e)
            return pd.DataFrame()

    # -- Trading events ----------------------------------------------------

    def get_billboard_list(self, start_date: str, end_date: str = None) -> pd.DataFrame:
        """Fetch dragon-tiger list via AKShare ``stock_lhb_detail_em``."""
        self._require_available()
        try:
            fmt_date = self._normalize_date(start_date) or pd.Timestamp.today().strftime("%Y%m%d")
            df = self._ak.stock_lhb_detail_em(start_date=fmt_date, end_date=fmt_date)
            if df is None or df.empty:
                return pd.DataFrame()
            col_map = {
                "代码": "code",
                "名称": "name",
                "最新价": "close",
                "涨跌幅": "change_pct",
                "换手率": "turnover_rate",
                "成交额": "amount",
                "龙虎榜净买额": "net_inflow",
                "买入额": "buy_amount",
                "卖出额": "sell_amount",
                "上榜原因": "reason",
            }
            df = self._normalize_df_columns(df, col_map)
            if "code" in df.columns:
                df = df.set_index("code")
            return df
        except Exception as e:
            _log_api_error(f"get_billboard_list for {start_date}", e)
            return pd.DataFrame()

    def get_st_stocks(self) -> pd.DataFrame:
        """Fetch ST stock list via AKShare ``stock_zh_a_st_em``."""
        self._require_available()
        try:
            df = self._ak.stock_zh_a_st_em()
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            _log_api_error("get_st_stocks", e)
            return pd.DataFrame()

    def get_suspended_stocks(self) -> pd.DataFrame:
        """Fetch suspended stock list via AKShare ``stock_zh_a_stop_em``."""
        self._require_available()
        try:
            df = self._ak.stock_zh_a_stop_em()
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            _log_api_error("get_suspended_stocks", e)
            return pd.DataFrame()

    # -- Macro --------------------------------------------------------------

    def get_macro_raw(self, indicator: str) -> pd.DataFrame:
        """Fetch macro indicator via AKShare."""
        self._require_available()
        try:
            indicator = indicator.lower()
            if indicator == "shibor":
                df = self._ak.macro_china_shibor_all()
                date_col = "日期"
                val_col = "O/N-定价"
            elif indicator == "cpi":
                df = self._ak.macro_china_cpi()
                date_col = "月份"
                val_col = "当前值"
            elif indicator == "ppi":
                df = self._ak.macro_china_ppi()
                date_col = "月份"
                val_col = "今月"
            elif indicator == "pmi":
                df = self._ak.macro_china_pmi()
                date_col = "月份"
                val_col = "统计数据"
            elif indicator == "m2":
                df = self._ak.macro_china_money_supply()
                date_col = "月份"
                val_col = "M2(亿元)"
            else:
                logger.warning("Unsupported macro indicator: %s", indicator)
                return pd.DataFrame()
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns={date_col: "date", val_col: indicator})
            df = self._set_datetime_index(df, "date")
            df = self._to_numeric_cols(df, [indicator])
            return df.sort_index()
        except Exception as e:
            _log_api_error(f"get_macro_raw for {indicator}", e)
            return pd.DataFrame()

    def get_cpi_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_macro_raw("cpi")

    def get_ppi_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_macro_raw("ppi")

    def get_pmi_index(self, start_date: str, end_date: str, **kwargs) -> pd.DataFrame:
        return self.get_macro_raw("pmi")

    def get_m2_supply(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_macro_raw("m2")

    # -- Health & info ------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ok" if self._available else "degraded",
            "akshare_available": self._available,
        }

    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.source_type,
            "description": "EastMoney data source adapter (via AKShare)",
            "akshare_available": self._available,
        }
