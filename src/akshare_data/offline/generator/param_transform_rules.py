"""参数转换规则"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class ParamTransformRules:
    """参数转换规则"""

    EXACT_MATCH_RULES: Dict[str, Tuple[str, List[str]]] = {
        "symbol": ("prepend_prefix:sh/sz", ["stock", "fund", "index", "etf", "lof"]),
        "stock_code": ("prepend_prefix:sh/sz", ["stock"]),
        "fund_code": ("prepend_prefix:sh/sz", ["fund"]),
        "index_code": ("prepend_prefix:sh/sz", ["index"]),
    }

    PATTERN_RULES: List[Tuple[str, str, List[str]]] = [
        (r"start_date|end_date|date", "YYYYMMDD", ["*"]),
        (r"year", "YYYY", ["*"]),
        (r"month", "YYYYMM", ["*"]),
        (r"adjust", "pass_through", ["*"]),
        (r"period", "daily", ["daily", "weekly", "monthly"]),
        (r"timeout", "pass_through", ["*"]),
    ]

    CATEGORY_TRANSFORMS: Dict[str, List[str]] = {
        "equity": ["symbol", "start_date", "end_date", "adjust"],
        "fund": ["symbol", "start_date", "end_date", "adjust", "period"],
        "index": ["symbol", "start_date", "end_date"],
        "futures": ["symbol", "start_date", "end_date", "period"],
        "options": ["symbol", "start_date", "end_date"],
        "macro": ["start_date", "end_date"],
        "bond": ["symbol", "start_date", "end_date"],
    }

    def infer(
        self,
        signature: List[str],
        category: Optional[str] = None,
    ) -> Dict[str, str]:
        """从 signature 和 category 推断 param_transforms"""
        result = {}

        for param in signature:
            transform = self._infer_single_param(param, category)
            if transform:
                result[param] = transform

        return result

    def _infer_single_param(
        self,
        param_name: str,
        category: Optional[str] = None,
    ) -> Optional[str]:
        """推断单个参数的类型"""
        if param_name in self.EXACT_MATCH_RULES:
            transform, categories = self.EXACT_MATCH_RULES[param_name]
            if category is None or any(c in (category or "") for c in categories):
                return transform
            return None

        for pattern, transform, categories in self.PATTERN_RULES:
            if re.search(pattern, param_name.lower()):
                if category is None or any(c in (category or "") for c in categories):
                    return transform

        return None

    def get_transform_for_param(
        self,
        param_name: str,
        func_name: Optional[str] = None,
    ) -> Optional[str]:
        """获取特定参数的转换规则"""
        if func_name:
            for prefix, transform in [
                ("stock_zh_a_", "prepend_prefix:sh/sz"),
                ("stock_zh_index_", "prepend_prefix:sh/sz"),
                ("fund_etf_", "prepend_prefix:sh/sz"),
                ("fund_lof_", "prepend_prefix:sh/sz"),
                ("futures_zh_", "pass_through"),
            ]:
                if func_name.startswith(prefix):
                    if param_name == "symbol":
                        return transform

        return self._infer_single_param(param_name)