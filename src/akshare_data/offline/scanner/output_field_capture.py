"""输出字段捕获器 - 捕获函数返回的列信息"""

from __future__ import annotations

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import pandas as pd

from akshare_data.offline.scanner.column_type_inferrer import ColumnTypeInferrer
from akshare_data.offline.scanner.code_parser import CodeParser

logger = logging.getLogger("akshare_data")

DEFAULT_TIMEOUT_SECONDS = 10

# 按函数名前缀的超时配置（秒）
TIMEOUT_BY_PREFIX = {
    "article_": 30,
    "fred_": 30,
    "currency_pair_map": 30,
    "currency_currencies": 30,
    "energy_carbon_": 30,
    "forbes_": 30,
    "index_bloomberg_": 30,
    "index_csindex_": 15,
    "futures_foreign_": 15,
    "futures_shfe_warehouse_receipt": 15,
    "bond_cb_index_jsl": 15,
    "fund_etf_spot_ths": 10,
}

# 需要特殊符号参数的函数
SPECIAL_SYMBOL_FUNCS = {
    "article_epu_index": "China",
    "article_oman_rv": "FTSE",
    "article_oman_rv_short": "SPX",
    "article_rlab_rv": "000001",
    "forbes_rank": "2021福布斯中国创投人100",
    "currency_pair_map": "美元",
    "currency_currencies": "USD",
    "bond_cb_index_jsl": "",
    "bond_zh_hs_cov_daily": "sz123123",
    "bond_zh_hs_cov_spot": "",
    "bond_china_yield": "",
    "air_quality_hist": "20200101",
    "air_quality_rank": "20200101",
    "air_quality_watch_point": "20200101",
    "macro_china_cpi_monthly": "",
    "macro_china_cpi_yearly": "",
    "macro_china_gdp_yearly": "",
}

# 不需要参数的函数（无参数调用）
NO_PARAM_FUNCS = {
    "tool_trade_date_hist_sina",
    "stock_zh_a_spot_em",
    "stock_zh_a_spot",
    "fund_etf_spot_em",
    "fund_lof_spot_em",
    "index_zh_a_spot_em",
    "bond_zh_cov",
    "bond_zh_hs_cov_spot",
}


@dataclass
class OutputColumn:
    """输出列信息"""
    name: str
    inferred_type: str = "str"
    source: str = "unknown"
    description: str = ""


class OutputFieldCapture:
    """捕获函数返回的列信息"""

    def __init__(self):
        self.type_inferrer = ColumnTypeInferrer()
        self.code_parser = CodeParser(self.type_inferrer)
        self._func_cache: Dict[str, Callable] = {}
        self._failed_funcs: Set[str] = set()
        self._runtime_capture_stats: Dict[str, int] = {
            "success": 0,
            "timeout": 0,
            "failed": 0,
            "non_df": 0,
        }
        self._setup_proxy()

    def _setup_proxy(self):
        """设置代理环境变量"""
        http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if http_proxy or https_proxy:
            logger.info(f"Using proxy: http={http_proxy}, https={https_proxy}")

    def get_timeout_for_func(self, func_name: str) -> int:
        """根据函数名获取超时时间"""
        for prefix, timeout in TIMEOUT_BY_PREFIX.items():
            if func_name.startswith(prefix):
                return timeout
        return DEFAULT_TIMEOUT_SECONDS

    def capture(
        self,
        func_name: str,
        signature: List[str],
        params: Dict[str, Any],
        use_cache: bool = True,
        category: Optional[str] = None,
    ) -> List[OutputColumn]:
        """捕获函数返回的列信息

        策略:
        1. 首先从代码解析列名
        2. 如果无法解析，尝试运行时捕获
        3. 如果仍然失败，返回空列表
        """
        if use_cache and func_name in self._failed_funcs:
            return []

        columns = self._capture_from_code(func_name, signature)
        if columns:
            logger.debug(f"Captured {len(columns)} columns from code for {func_name}")
            return columns

        timeout = self.get_timeout_for_func(func_name)
        columns = self._capture_runtime(func_name, params, timeout)
        if columns:
            logger.debug(f"Captured {len(columns)} columns from runtime for {func_name}")
            return columns

        self._failed_funcs.add(func_name)
        return []

    def get_stats(self) -> Dict[str, int]:
        """获取运行时捕获统计"""
        return {
            **self._runtime_capture_stats,
            "failed_funcs": len(self._failed_funcs),
        }

    def _capture_from_code(self, func_name: str, signature: List[str]) -> List[OutputColumn]:
        """从代码解析列名"""
        func_obj = self._get_func_obj(func_name)
        if not func_obj:
            return []

        parsed_columns = self.code_parser.parse(func_obj)
        return [
            OutputColumn(
                name=col.name,
                inferred_type=col.inferred_type,
                source="code_parse",
                description=col.description,
            )
            for col in parsed_columns
        ]

    def _capture_runtime(
        self,
        func_name: str,
        params: Dict[str, Any],
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> List[OutputColumn]:
        """运行时捕获列名（跨平台超时实现）"""
        func_obj = self._get_func_obj(func_name)
        if not func_obj:
            return []

        call_params = self._prepare_params(func_obj, params, func_name)
        if call_params is None:
            return []

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func_obj, **call_params)
                result = future.result(timeout=timeout)

            if isinstance(result, pd.DataFrame):
                if result.empty:
                    self._runtime_capture_stats["failed"] += 1
                    logger.debug(f"Empty DataFrame returned for {func_name}")
                    return []

                columns = []
                for col_name in result.columns:
                    col_type = self._infer_df_column_type(result[col_name])
                    columns.append(
                        OutputColumn(
                            name=str(col_name),
                            inferred_type=col_type,
                            source="runtime_capture",
                            description="",
                        )
                    )
                self._runtime_capture_stats["success"] += 1
                return columns
            else:
                self._runtime_capture_stats["non_df"] += 1
                logger.debug(f"Non-DataFrame return from {func_name}: {type(result).__name__}")
        except FuturesTimeoutError:
            self._runtime_capture_stats["timeout"] += 1
            logger.warning(f"Timeout capturing {func_name} after {timeout}s")
        except Exception as e:
            self._runtime_capture_stats["failed"] += 1
            logger.debug(f"Runtime capture failed for {func_name}: {e}")

        return []

    def _get_func_obj(self, func_name: str) -> Optional[Callable]:
        """获取函数对象"""
        if func_name in self._func_cache:
            return self._func_cache[func_name]

        try:
            import akshare as ak
            func_obj = getattr(ak, func_name, None)
            if func_obj:
                self._func_cache[func_name] = func_obj
            return func_obj
        except ImportError:
            return None

    def _prepare_params(
        self,
        func: Callable,
        params: Dict[str, Any],
        func_name: str,
    ) -> Optional[Dict[str, Any]]:
        """准备函数调用参数"""
        import inspect

        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            return None

        call_params = {}

        if func_name in NO_PARAM_FUNCS:
            return {}

        if func_name in SPECIAL_SYMBOL_FUNCS:
            special_value = SPECIAL_SYMBOL_FUNCS[func_name]
            if special_value:
                first_param_name = list(sig.parameters.keys())[0] if sig.parameters else None
                if first_param_name:
                    call_params[first_param_name] = special_value
                    return call_params
            else:
                return {}

        for param_name, param_obj in sig.parameters.items():
            if param_name in params:
                value = params[param_name]
                if self._is_valid_param_value(value):
                    call_params[param_name] = value
            elif param_obj.default is not inspect.Parameter.empty:
                pass
            else:
                default_value = self._get_default_for_param(param_name, func_name)
                if default_value is not None:
                    call_params[param_name] = default_value

        return call_params if call_params else None

    def _is_valid_param_value(self, value: Any) -> bool:
        """验证参数值是否有效"""
        if value is None:
            return False
        value_str = str(value)

        if len(value_str) > 200:
            return False

        if value_str.startswith(('http://', 'https://')):
            return False

        if '&' in value_str and '=' in value_str:
            if not value_str.startswith('&'):
                return False

        invalid_chars = set('()/+^*[]{}')
        if any(c in invalid_chars for c in value_str):
            return False

        return True

    def _get_default_for_param(self, param_name: str, func_name: str) -> Optional[Any]:
        """获取参数的默认值"""
        param_lower = param_name.lower()
        date_patterns = ["date", "start", "end"]
        if any(p in param_lower for p in date_patterns):
            if "start" in param_lower:
                return (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            return datetime.now().strftime("%Y%m%d")

        if "symbol" in param_lower or "code" in param_lower:
            if "fund" in func_name:
                return "510300"
            if "index" in func_name:
                return "000001"
            if "stock" in func_name:
                return "000001"
            return "000001"

        if "period" in param_lower:
            return "daily"

        if "adjust" in param_lower:
            return "qfq"

        if "market" in param_lower:
            return "sh"

        return None

    def _infer_df_column_type(self, series: pd.Series) -> str:
        """从 DataFrame 列推断类型"""
        dtype_str = str(series.dtype)

        if "datetime" in dtype_str or "date" in dtype_str:
            return "datetime"
        if "int" in dtype_str:
            return "int"
        if "float" in dtype_str or "double" in dtype_str:
            return "float"

        if series.dtype == "object":
            sample = series.dropna().head(10)
            if not sample.empty:
                first_val = sample.iloc[0]
                if isinstance(first_val, (int, float)):
                    return "float"
                if isinstance(first_val, datetime):
                    return "datetime"

        return "str"