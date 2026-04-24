"""输出字段捕获器 - 捕获函数返回的列信息"""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import pandas as pd

from akshare_data.offline.scanner.column_type_inferrer import ColumnTypeInferrer
from akshare_data.offline.scanner.code_parser import CodeParser

logger = logging.getLogger("akshare_data")

TIMEOUT_SECONDS = 5


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

    def capture(
        self,
        func_name: str,
        signature: List[str],
        params: Dict[str, Any],
        use_cache: bool = True,
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

        columns = self._capture_runtime(func_name, params)
        if columns:
            logger.debug(f"Captured {len(columns)} columns from runtime for {func_name}")
            return columns

        self._failed_funcs.add(func_name)
        logger.warning(f"Failed to capture output fields for {func_name}")
        return []

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
    ) -> List[OutputColumn]:
        """运行时捕获列名（跨平台超时实现）"""
        func_obj = self._get_func_obj(func_name)
        if not func_obj:
            return []

        params = self._prepare_params(func_obj, params)
        if params is None:
            return []

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func_obj, **params)
                result = future.result(timeout=TIMEOUT_SECONDS)

            if isinstance(result, pd.DataFrame) and not result.empty:
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
                return columns
        except FuturesTimeoutError:
            logger.warning(f"Timeout capturing {func_name} after {TIMEOUT_SECONDS}s")
        except Exception as e:
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
    ) -> Optional[Dict[str, Any]]:
        """准备函数调用参数"""
        import inspect

        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            return None

        call_params = {}
        for param_name, param_obj in sig.parameters.items():
            if param_name in params:
                value = params[param_name]
                if self._is_valid_param_value(value):
                    call_params[param_name] = value
            elif param_obj.default is not inspect.Parameter.empty:
                pass
            else:
                default_value = self._get_default_for_param(param_name)
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

    def _get_default_for_param(self, param_name: str) -> Optional[Any]:
        """获取参数的默认值"""
        date_patterns = ["date", "start", "end"]
        param_lower = param_name.lower()
        if any(p in param_lower for p in date_patterns):
            if "start" in param_lower:
                return (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            return datetime.now().strftime("%Y%m%d")

        symbol_patterns = ["symbol", "code", "stock"]
        if any(p in param_lower for p in symbol_patterns):
            return "000001"

        if "period" in param_lower:
            return "daily"

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