"""语义推断器 - 将中文字段名转换为业务字段名"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("akshare_data")


# 常用字段映射字典
FIELD_MAPPING_DICT = {
    # 日期时间
    "日期": "date",
    "时间": "datetime",
    "交易日期": "trade_date",
    "日期时间": "datetime",
    
    # 价格
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "昨收": "prev_close",
    "今开": "open",
    
    # 成交量额
    "成交量": "volume",
    "成交额": "amount",
    "成交": "volume",
    "金额": "amount",
    
    # 涨跌
    "涨跌幅": "change_pct",
    "涨跌额": "change",
    "涨跌": "change",
    "涨幅": "change_pct",
    
    # 代码名称
    "代码": "code",
    "名称": "name",
    "股票代码": "symbol",
    "股票名称": "stock_name",
    "债券代码": "bond_code",
    "债券名称": "bond_name",
    "基金代码": "fund_code",
    "基金名称": "fund_name",
    
    # 市值指标
    "总市值": "total_mv",
    "流通市值": "float_mv",
    "市值": "market_cap",
    
    # 比率指标
    "换手率": "turnover_rate",
    "市盈率": "pe_ratio",
    "市净率": "pb_ratio",
    "振幅": "amplitude",
    
    # 数量
    "数量": "quantity",
    "手数": "lot_size",
    "笔数": "trade_count",
    
    # 价格相关
    "价格": "price",
    "最新价": "latest_price",
    "现价": "current_price",
    "均价": "avg_price",
    
    # 利率相关
    "利率": "interest_rate",
    "收益率": "yield_rate",
    "年化收益率": "annual_yield",
}


class SemanticInferrer:
    """语义推断器：将中文字段名转换为英文业务字段名"""

    def __init__(self):
        self.field_mapping = FIELD_MAPPING_DICT
        self.custom_mappings = {}  # 用户自定义映射

    def infer_field_name(
        self,
        chinese_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """推断字段名"""
        # 1. 精确匹配
        if chinese_name in self.field_mapping:
            return self.field_mapping[chinese_name]
        
        if chinese_name in self.custom_mappings:
            return self.custom_mappings[chinese_name]
        
        # 2. 包含匹配
        for cn, en in self.field_mapping.items():
            if cn in chinese_name:
                # 提取前缀或后缀
                if chinese_name.startswith(cn):
                    suffix = chinese_name[len(cn):]
                    suffix_en = self._infer_suffix(suffix)
                    return f"{en}_{suffix_en}" if suffix_en else en
                elif chinese_name.endswith(cn):
                    prefix = chinese_name[:-len(cn)]
                    prefix_en = self._infer_prefix(prefix)
                    return f"{prefix_en}_{en}" if prefix_en else en
        
        # 3. 拼音转换（简单版）
        return self._chinese_to_pinyin(chinese_name)

    def batch_infer(
        self,
        field_names: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """批量推断字段名"""
        return {
            cn: self.infer_field_name(cn, context)
            for cn in field_names
        }

    def _infer_prefix(self, prefix: str) -> Optional[str]:
        """推断前缀"""
        prefix_map = {
            "前": "prev",
            "后": "next",
            "今": "current",
            "昨": "yesterday",
            "明": "tomorrow",
            "本": "current",
            "上": "prev",
            "下": "next",
            "最": "max",
            "最": "min",
        }
        return prefix_map.get(prefix)

    def _infer_suffix(self, suffix: str) -> Optional[str]:
        """推断后缀"""
        suffix_map = {
            "率": "rate",
            "额": "amount",
            "量": "volume",
            "价": "price",
            "数": "count",
            "比": "ratio",
            "值": "value",
        }
        return suffix_map.get(suffix)

    def _chinese_to_pinyin(self, chinese: str) -> str:
        """中文转拼音（简单版）"""
        # 这里可以使用 pypinyin 库，这里用简化版
        # 提取数字和字母
        alphanumeric = re.sub(r'[^\w]', '', chinese)
        
        if alphanumeric:
            return alphanumeric.lower()
        
        # 如果全是中文，返回默认名称
        return f"field_{hash(chinese) % 10000}"

    def add_custom_mapping(self, chinese: str, english: str):
        """添加自定义映射"""
        self.custom_mappings[chinese] = english
        logger.info(f"Added custom mapping: {chinese} -> {english}")

    def infer_with_llm(
        self,
        chinese_name: str,
        context: Dict[str, Any],
    ) -> str:
        """使用 LLM 推断（需要实现 LLM 接口）"""
        # TODO: 实现 LLM 推断
        # prompt = f"""
        # 将以下中文字段名转换为英文业务字段名：
        # - 字段名：{chinese_name}
        # - 上下文：{context.get('function_description', '')}
        # - 数据类型：{context.get('dtype', '')}
        # - 示例值：{context.get('sample_values', [])}
        # 
        # 要求：
        # 1. 使用 snake_case 命名
        # 2. 语义化，符合金融数据惯例
        # 3. 简洁明了
        # 
        # 只返回字段名，不要解释。
        # """
        # 
        # response = llm_client.generate(prompt)
        # return response.strip()
        
        return self.infer_field_name(chinese_name, context)


# 使用示例
if __name__ == "__main__":
    inferrer = SemanticInferrer()
    
    # 测试字段推断
    test_fields = [
        "日期",
        "开盘",
        "收盘",
        "成交量",
        "涨跌幅",
        "股票代码",
        "换手率",
        "前收盘价",
        "今成交量",
    ]
    
    for field in test_fields:
        inferred = inferrer.infer_field_name(field)
        print(f"{field:15s} -> {inferred}")