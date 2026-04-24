"""列类型推断器 - 根据列名推断数据类型"""

from __future__ import annotations

from typing import Any, Dict, List, Set


class ColumnTypeInferrer:
    """根据列名推断数据类型"""

    TYPE_PATTERNS: Dict[str, List[str]] = {
        "datetime": [
            "日期", "date", "时间", "time", "月份", "month", "年份", "year",
            "日", "day", "季度", "quarter", "week", "周", "period", "期限",
            "到期", "maturity", "到期日", "上市", "交易日期", "报告日期",
            "更新日期", "结算日期", "交割日期", "申购日期", "中签号发布日",
        ],
        "float": [
            "价", "price", "open", "close", "high", "low", "量", "volume",
            "额", "amount", "rate", "率", "pct", "涨幅", "涨跌", "市值",
            "委", "买", "卖", "bid", "ask", "index", "指数", "eps", "pe",
            "pb", "股息", "yield", "规模", "scale", "净资产", "净值",
            "增长率", "增长", "溢价", "贴水", "利息", "成本", "费用",
            "佣金", "手续费", "保证金", "面值", "发行价", "中签率",
        ],
        "int": [
            "代码", "code", "编号", "num", "数量", "count", "数量",
            "股份", "股本", "股数", "份额", "张", "手", "户", "户数",
            "人", "人数", "排名", "rank", "位", "占比", "比例",
        ],
        "str": [
            "名称", "name", "类型", "type", "status", "简称", "symbol",
            "market", "市场", "交易所", "exchange", "板块", "sector",
            "行业", "industry", "概念", "concept", "风格", "风格",
            "评级", "rating", "信用", "credit", "期限", "term",
            "到期时间", "剩余期限",
        ],
    }

    def __init__(self):
        self._pattern_map: Dict[str, Set[str]] = {}
        for dtype, patterns in self.TYPE_PATTERNS.items():
            self._pattern_map[dtype] = set(p.lower() for p in patterns)

    def infer(self, col_name: str) -> str:
        """根据列名推断类型"""
        col_lower = col_name.lower()

        for dtype, pattern_set in self._pattern_map.items():
            for pattern in pattern_set:
                if pattern in col_lower:
                    return dtype

        if self._contains_numeric(col_name):
            return "float"
        if self._is_date_like(col_name):
            return "datetime"

        return "str"

    def _contains_numeric(self, col_name: str) -> bool:
        """检查是否包含数值相关词汇"""
        numeric_keywords = ["率", "额", "量", "价", "值", "涨", "跌", "高", "低"]
        return any(kw in col_name for kw in numeric_keywords)

    def _is_date_like(self, col_name: str) -> bool:
        """检查是否是日期相关"""
        date_keywords = ["日期", "时间", "日", "月", "年", "date", "time", "day"]
        return any(kw in col_name.lower() for kw in date_keywords)

    def infer_from_value(self, value: Any) -> str:
        """根据实际值推断类型"""
        if value is None:
            return "str"

        value_type = type(value).__name__

        type_map = {
            "datetime": ["datetime", "Timestamp"],
            "date": ["date"],
            "int": ["int", "int64", "int32", "int16", "int8"],
            "float": ["float", "float64", "float32", "float16"],
        }

        for dtype, types in type_map.items():
            if value_type in types:
                return dtype

        return "str"