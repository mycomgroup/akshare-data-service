"""参数转换规则"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


CATEGORY_HIERARCHY: Dict[str, List[str]] = {
    "equity": ["stock", "fund", "index", "etf", "lof"],
    "fund": ["fund", "etf", "lof"],
    "index": ["index"],
    "futures": ["futures"],
    "options": ["options"],
    "macro": ["macro"],
    "bond": ["bond"],
    "market": ["stock", "fund", "index", "etf", "lof", "futures", "options", "bond"],
    "other": ["*"],
}


def _category_matches(check_category: Optional[str], allowed_categories: List[str]) -> bool:
    """检查 check_category 是否与 allowed_categories 中的任一类别匹配"""
    if check_category is None:
        return True
    if "*" in allowed_categories:
        return True
    if not check_category:
        return True

    check_category = check_category.lower()
    for allowed in allowed_categories:
        allowed_lower = allowed.lower()
        if allowed_lower == check_category:
            return True
        if check_category in CATEGORY_HIERARCHY:
            siblings = CATEGORY_HIERARCHY[check_category]
            if allowed_lower in siblings:
                return True
        if allowed_lower in CATEGORY_HIERARCHY:
            siblings = CATEGORY_HIERARCHY[allowed_lower]
            if check_category in siblings:
                return True
    return False


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
            if _category_matches(category, categories):
                return transform
            return None

        for pattern, transform, categories in self.PATTERN_RULES:
            if re.search(pattern, param_name.lower()):
                if _category_matches(category, categories):
                    return transform

        return None

        for pattern, transform, categories in self.PATTERN_RULES:
            if re.search(pattern, param_name.lower()):
                if category is None or any(c in (category or "") for c in categories):
                    return transform

        return None

    def _is_futures_func(self, func_name: Optional[str]) -> bool:
        """检查是否是期货相关函数"""
        if not func_name:
            return False
        return any(func_name.startswith(p) for p in self.FUTURES_PREFIXES)

    def get_transform_for_param(
        self,
        param_name: str,
        func_name: Optional[str] = None,
    ) -> Optional[str]:
        """获取特定参数的转换规则"""
        if func_name:
            if self._is_futures_func(func_name):
                if param_name == "symbol":
                    return "pass_through"

            if func_name.startswith("stock_zh_a_") or func_name.startswith("stock_zh_index_"):
                if param_name == "symbol":
                    return "prepend_prefix:sh/sz"
            elif func_name.startswith("fund_etf_") or func_name.startswith("fund_lof_"):
                if param_name == "symbol":
                    return "prepend_prefix:sh/sz"

        return self._infer_single_param(param_name)