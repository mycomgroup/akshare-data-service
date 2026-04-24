"""Interface Skeleton 生成器"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from akshare_data.offline.generator.name_normalizer import NameNormalizer
from akshare_data.offline.generator.param_transform_rules import ParamTransformRules

logger = logging.getLogger("akshare_data")

# 模块路径到 source name 的映射
_MODULE_SOURCE_MAP: Dict[str, str] = {
    "akshare.stock.stock_zh_a_sina": "akshare_sina",
    "akshare.stock.stock_zh_a_tick_tx": "akshare_sina",
    "akshare.stock.stock_zh_a_tx": "akshare_sina",
    "akshare.stock.stock_zh_ah_tx": "akshare_sina",
    "akshare.stock.stock_zh_b_sina": "akshare_sina",
    "akshare.stock.stock_zh_kcb_sina": "akshare_sina",
    "akshare.stock.stock_intraday_sina": "akshare_sina",
    "akshare.stock_feature.stock_hist_em": "akshare_em",
    "akshare.stock_feature.stock_board_concept_ths": "akshare_ths",
    "akshare.stock_feature.stock_board_industry_ths": "akshare_ths",
    "akshare.stock_feature.stock_technology_ths": "akshare_ths",
    "akshare.stock_feature.stock_fhps_ths": "akshare_ths",
    "akshare.stock_feature.stock_cyq_em": "akshare_em",
    "akshare.stock_feature.stock_lhb_em": "akshare_em",
    "akshare.stock_feature.stock_lhb_sina": "akshare_sina",
    "akshare.stock_feature.stock_margin_em": "akshare_em",
    "akshare.stock_feature.stock_margin_sse": "akshare_em",
    "akshare.stock_feature.stock_esg_sina": "akshare_sina",
    "akshare.stock.stock_industry_cninfo": "akshare_cninfo",
    "akshare.stock.stock_dividend_cninfo": "akshare_cninfo",
    "akshare.stock.stock_profile_cninfo": "akshare_cninfo",
    "akshare.stock.stock_share_changes_cninfo": "akshare_cninfo",
    "akshare.stock.stock_hold_control_cninfo": "akshare_cninfo",
    "akshare.stock.stock_hold_num_cninfo": "akshare_cninfo",
    "akshare.stock.stock_ipo_summary_cninfo": "akshare_cninfo",
    "akshare.stock.stock_yjyg_cninfo": "akshare_cninfo",
    "akshare.stock.stock_disclosure_cninfo": "akshare_cninfo",
    "akshare.stock.stock_irm_cninfo": "akshare_cninfo",
    "akshare.stock.stock_xq": "akshare_xq",
    "akshare.stock.stock_weibo_nlp": "akshare_xq",
    "akshare.stock.stock_hot_rank_em": "akshare_em",
    "akshare.stock.stock_hot_up_em": "akshare_em",
    "akshare.stock.stock_hot_search_baidu": "akshare_baidu",
    "akshare.stock.stock_news_cx": "akshare_cx",
    "akshare.stock.stock_zh_comparison_em": "akshare_em",
    "akshare.stock.stock_hk_comparison_em": "akshare_em",
    "akshare.stock.stock_hk_sina": "akshare_sina",
    "akshare.stock.stock_hk_famous": "akshare_sina",
    "akshare.stock.stock_hk_fhpx_ths": "akshare_ths",
    "akshare.stock.stock_hk_hot_rank_em": "akshare_em",
    "akshare.stock.stock_us_sina": "akshare_sina",
    "akshare.stock.stock_us_js": "akshare_sina",
    "akshare.stock.stock_us_pink": "akshare_sina",
    "akshare.stock.stock_us_famous": "akshare_sina",
    "akshare.stock.stock_info_em": "akshare_em",
    "akshare.stock.stock_info": "akshare_sina",
    "akshare.stock.stock_summary": "akshare_sina",
    "akshare.stock.stock_stop": "akshare_em",
    "akshare.stock.stock_dzjy_em": "akshare_em",
    "akshare.stock.stock_fund_em": "akshare_em",
    "akshare.stock.stock_fund_hold": "akshare_em",
    "akshare.stock.stock_gsrl_em": "akshare_em",
    "akshare.stock.stock_hsgt_em": "akshare_em",
    "akshare.stock.stock_industry": "akshare_sina",
    "akshare.stock.stock_industry_sw": "akshare_sina",
    "akshare.stock.stock_industry_pe_cninfo": "akshare_cninfo",
    "akshare.stock.stock_intraday_em": "akshare_em",
    "akshare.stock.stock_new_cninfo": "akshare_cninfo",
    "akshare.stock.stock_profile_em": "akshare_em",
    "akshare.stock.stock_rank_forecast": "akshare_em",
    "akshare.stock.stock_repurchase_em": "akshare_em",
    "akshare.stock.stock_ask_bid_em": "akshare_em",
    "akshare.stock.stock_board_concept_em": "akshare_em",
    "akshare.stock.stock_board_industry_em": "akshare_em",
    "akshare.stock.stock_cg_equity_mortgage": "akshare_em",
    "akshare.stock.stock_cg_guarantee": "akshare_em",
    "akshare.stock.stock_cg_lawsuit": "akshare_em",
    "akshare.stock_fundamental.stock_basic_info_xq": "akshare_xq",
    "akshare.stock_fundamental.stock_finance_sina": "akshare_sina",
    "akshare.stock_fundamental.stock_finance_ths": "akshare_ths",
    "akshare.stock_fundamental.stock_finance_hk_em": "akshare_em",
    "akshare.stock_fundamental.stock_finance_us_em": "akshare_em",
    "akshare.stock_fundamental.stock_gbjg_em": "akshare_em",
    "akshare.stock_fundamental.stock_hold": "akshare_em",
    "akshare.stock_fundamental.stock_ipo_declare": "akshare_em",
    "akshare.stock_fundamental.stock_ipo_review": "akshare_em",
    "akshare.stock_fundamental.stock_ipo_ths": "akshare_ths",
    "akshare.stock_fundamental.stock_ipo_tutor": "akshare_em",
    "akshare.stock_fundamental.stock_kcb_detail_sse": "akshare_em",
    "akshare.stock_fundamental.stock_kcb_sse": "akshare_em",
    "akshare.stock_fundamental.stock_notice": "akshare_em",
    "akshare.stock_fundamental.stock_profit_forecast_em": "akshare_em",
    "akshare.stock_fundamental.stock_profit_forecast_hk_etnet": "akshare_em",
    "akshare.stock_fundamental.stock_profit_forecast_ths": "akshare_ths",
    "akshare.stock_fundamental.stock_recommend": "akshare_sina",
    "akshare.stock_fundamental.stock_register_em": "akshare_em",
    "akshare.stock_fundamental.stock_restricted_em": "akshare_em",
    "akshare.stock_fundamental.stock_zygc": "akshare_em",
    "akshare.stock_fundamental.stock_zyjs_ths": "akshare_ths",
    "akshare.fund.fund_etf_em": "akshare_em",
    "akshare.fund.fund_lof_em": "akshare_em",
    "akshare.fund.fund_open_em": "akshare_em",
    "akshare.fund.fund_manager_em": "akshare_em",
    "akshare.fund.fund_portfolio_em": "akshare_em",
    "akshare.fund.fund_rating_em": "akshare_em",
    "akshare.fund.fund_fhps_em": "akshare_em",
    "akshare.fund.fund_cf_em": "akshare_em",
    "akshare.fund.fund_fh_em": "akshare_em",
    "akshare.fund.fund_fh_rank_em": "akshare_em",
    "akshare.fund.fund_aum_em": "akshare_em",
    "akshare.fund.fund_exchange_rank_em": "akshare_em",
    "akshare.fund.fund_hk_rank_em": "akshare_em",
    "akshare.fund.fund_money_rank_em": "akshare_em",
    "akshare.fund.fund_rank_em": "akshare_em",
    "akshare.fund.fund_value_em": "akshare_em",
    "akshare.fund.fund_etf_sina": "akshare_sina",
    "akshare.fund.fund_etf_ths": "akshare_ths",
    "akshare.fund.fund_portfolio_sina": "akshare_sina",
    "akshare.fund.fund_portfolio_ths": "akshare_ths",
    "akshare.index.index_zh_a": "akshare_sina",
    "akshare.index.index_zh_a_hist": "akshare_em",
    "akshare.index.index_bloomberg": "akshare_em",
    "akshare.index.index_investing_global": "akshare_em",
    "akshare.index.index_spot_em": "akshare_em",
    "akshare.index.index_hist_em": "akshare_em",
    "akshare.index.index_realtime_em": "akshare_em",
    "akshare.bond.bond_zh_hs": "akshare_sina",
    "akshare.bond.bond_zh_hs_daily": "akshare_sina",
    "akshare.bond.bond_zh_hs_spot": "akshare_sina",
    "akshare.bond.bond_zh_hs_min": "akshare_sina",
    "akshare.bond.bond_zh_hs_cov_daily": "akshare_sina",
    "akshare.bond.bond_zh_hs_cov_spot": "akshare_sina",
    "akshare.bond.bond_zh_hs_cov_min": "akshare_sina",
    "akshare.bond.bond_zh_cov": "akshare_em",
    "akshare.bond.bond_zh_cov_info": "akshare_em",
    "akshare.bond.bond_cash_summary_sse": "akshare_em",
    "akshare.bond.bond_deal_summary_sse": "akshare_em",
    "akshare.bond.bond_info_cm": "akshare_em",
    "akshare.bond.bond_info_cm_detail": "akshare_em",
    "akshare.futures.futures_zh_daily_sina": "akshare_sina",
    "akshare.futures.futures_zh_spot": "akshare_sina",
    "akshare.futures.futures_zh_realtime": "akshare_sina",
    "akshare.futures.futures_zh_minute_sina": "akshare_sina",
    "akshare.futures.futures_main_sina": "akshare_sina",
    "akshare.futures.futures_inventory_em": "akshare_em",
    "akshare.futures.futures_spot_price_daily": "akshare_em",
    "akshare.futures.futures_spot_price": "akshare_em",
    "akshare.futures.futures_czce_daily": "akshare_em",
    "akshare.futures.futures_shfe_daily": "akshare_em",
    "akshare.futures.futures_dce_daily": "akshare_em",
    "akshare.futures.futures_cffex_daily": "akshare_em",
    "akshare.futures.futures_gfex_daily": "akshare_em",
    "akshare.futures.futures_spot_em": "akshare_em",
    "akshare.futures.futures_hist_em": "akshare_em",
    "akshare.futures.futures_display_main_sina": "akshare_sina",
    "akshare.option.option_sina": "akshare_sina",
    "akshare.option.option_finance_sina": "akshare_sina",
    "akshare.option.option_cffex_hs300_list_sina": "akshare_sina",
    "akshare.option.option_cffex_hs300_spot_sina": "akshare_sina",
    "akshare.option.option_cffex_hs300_daily_sina": "akshare_sina",
    "akshare.option.option_dce_daily": "akshare_em",
    "akshare.option.option_shfe_daily": "akshare_em",
    "akshare.option.option_czce_daily": "akshare_em",
    "akshare.option.option_gfex_daily": "akshare_em",
    "akshare.option.option_gzse_daily": "akshare_em",
    "akshare.macro.macro_china": "akshare_em",
    "akshare.macro.macro_usa": "akshare_em",
    "akshare.macro.macro_euro": "akshare_em",
    "akshare.macro.macro_japan": "akshare_em",
    "akshare.macro.macro_uk": "akshare_em",
    "akshare.macro.macro_china_gdp_yearly": "akshare_em",
    "akshare.macro.macro_china_cpi_yearly": "akshare_em",
    "akshare.macro.macro_china_ppi_yearly": "akshare_em",
    "akshare.macro.macro_china_pmi_yearly": "akshare_em",
    "akshare.macro.macro_china_money_supply": "akshare_em",
    "akshare.macro.macro_china_shrzgm": "akshare_em",
    "akshare.macro.macro_china_hk_cpi": "akshare_em",
    "akshare.macro.macro_china_hk_pmi": "akshare_em",
    "akshare.macro.macro_china_hk_cpi_monthly": "akshare_em",
    "akshare.economic.macro_bank_usa_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_euro_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_newzealand_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_switzerland_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_english_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_australia_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_japan_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_russia_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_india_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_brazil_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_china_interest_rate": "akshare_em",
    "akshare.economic.macro_bank_canada_interest_rate": "akshare_em",
    "akshare.spot.golden_bond_sina": "akshare_sina",
    "akshare.spot.quotation_sina": "akshare_sina",
    "akshare.spot.spot_golden_benchmark_sina": "akshare_sina",
    "akshare.spot.hog_rank_sina": "akshare_sina",
    "akshare.currency.currency_boc_sina": "akshare_sina",
    "akshare.currency.currency_sina": "akshare_sina",
    "akshare.currency.currency_pair_sina": "akshare_sina",
    "akshare.currency.currency_history": "akshare_em",
    "akshare.currency.currency_latest": "akshare_em",
    "akshare.currency.currency_currencies": "akshare_em",
    "akshare.currency.currency_history_range": "akshare_em",
    "akshare.reits.reits_realtime_em": "akshare_em",
    "akshare.reits.reits_hist_em": "akshare_em",
}


class InterfaceSkeletonGenerator:
    """从 registry entry 生成 interface skeleton"""

    def __init__(self):
        self.name_normalizer = NameNormalizer()
        self.param_transform_rules = ParamTransformRules()
        self._source_prefix_map = {
            "stock_": "akshare_sina",
            "fund_etf_": "akshare_em",
            "fund_lof_": "akshare_em",
            "index_": "akshare_em",
            "futures_": "akshare_em",
            "macro_": "akshare_em",
            "bond_": "akshare_em",
            "option_": "akshare_em",
            "currency_": "akshare_em",
            "economy_": "akshare_em",
            "spot_": "akshare_sina",
            "sw_": "akshare_sina",
            "lof_": "akshare_em",
            "fof_": "akshare_em",
            "hf_": "akshare_em",
            "reits_": "akshare_em",
        }
        # 统计信息
        self._stats: Dict[str, Any] = {
            "total_interfaces": 0,
            "with_output_fields": 0,
            "with_complete_mapping": 0,
            "with_partial_mapping": 0,
            "with_empty_mapping": 0,
            "noise_fields_filtered": 0,
            "by_source": {},
            "by_category": {},
        }

    def generate(
        self,
        registry_entry: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """生成 interface skeleton"""
        name = registry_entry["name"]
        signature = registry_entry.get("signature", [])
        output_fields = registry_entry.get("output_fields", [])
        category = registry_entry.get("category", "other")
        module_path = registry_entry.get("module", "")

        self._stats["total_interfaces"] += 1

        input_fields = self._generate_input(signature)
        output, mapping_quality = self._generate_output(output_fields)
        sources = self._generate_sources(name, signature, output_fields, category, module_path)
        param_transforms = self.param_transform_rules.infer(signature, category)

        # 统计 mapping 质量
        if output_fields:
            self._stats["with_output_fields"] += 1
            if mapping_quality == "complete":
                self._stats["with_complete_mapping"] += 1
            elif mapping_quality == "partial":
                self._stats["with_partial_mapping"] += 1
            else:
                self._stats["with_empty_mapping"] += 1

        # 统计 source 分布
        source_name = sources[0]["name"] if sources else "unknown"
        self._stats["by_source"][source_name] = self._stats["by_source"].get(source_name, 0) + 1

        # 统计 category 分布
        self._stats["by_category"][category] = self._stats["by_category"].get(category, 0) + 1

        skeleton = {
            "name": name,
            "category": category,
            "description": self._truncate_description(registry_entry.get("description", "")),
            "input": input_fields,
            "output": output,
            "rate_limit_key": registry_entry.get("rate_limit_key", "default"),
            "sources": sources,
        }

        if output_fields:
            skeleton["_generated_note"] = (
                f"# Auto-generated from akshare_registry.yaml\n"
                f"# TODO: 审核 output_mapping 和 param_transforms 是否正确 (mapping_quality: {mapping_quality})\n"
                f"# TODO: 根据需要添加 aliases 和 cache_table"
            )

        return skeleton

    def _generate_input(self, signature: List[str]) -> List[Dict]:
        """从 signature 生成 input 字段"""
        result = []
        for param in signature:
            inferred_type = self._infer_param_type(param)
            result.append({
                "name": param,
                "type": inferred_type,
                "required": True,
                "desc": f"{param} parameter",
            })
        return result

    def _generate_output(self, output_fields: List[Dict]) -> tuple:
        """从 output_fields 生成 output

        Returns:
            tuple: (output_list, mapping_quality)
            mapping_quality: "complete" | "partial" | "empty"
        """
        if not output_fields:
            return [], "empty"

        # 噪声字段模式
        noise_patterns = {
            '_', '-', '[', ']', '{', '}', '(', ')', '*', '+', '=', '/', '\\',
            ':', ';', ',', '.', '!', '?', '#', '@', '$', '%', '^', '&', '~',
            '`', '|', '"', "'", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'f', 's', 'u', 'v', 'c', 'p', 'n', 't', 'd', 'a', 'b', 'o', 'h', 'l',
            'result', 'results', 'data', 'df', 'ret', 'col', 'ms', 'zf', 'in', 'if',
        }

        result = []
        mapped_count = 0
        filtered_count = 0

        for field in output_fields:
            name = field["name"]

            # 过滤噪声字段
            if name.lower() in noise_patterns:
                filtered_count += 1
                continue

            # 过滤纯符号或过短且无意义的字段
            if len(name) <= 2 and not any('\u4e00' <= c <= '\u9fff' for c in name):
                if name.lower() not in {'date', 'open', 'high', 'low', 'close', 'pe', 'pb', 'nav', 'code', 'name', 'price', 'bid1', 'ask1', 'id', 'ip'}:
                    filtered_count += 1
                    continue

            normalized_name = self.name_normalizer.normalize(name)
            if normalized_name != name:
                mapped_count += 1
            result.append({
                "name": normalized_name,
                "type": field.get("type", "str"),
                "desc": field.get("description", "") or f"{normalized_name} field",
            })

        self._stats["noise_fields_filtered"] = self._stats.get("noise_fields_filtered", 0) + filtered_count

        # 计算映射质量
        total_count = len(result)
        if total_count == 0:
            quality = "empty"
        elif mapped_count == total_count:
            quality = "complete"
        elif mapped_count > 0:
            quality = "partial"
        else:
            quality = "empty"

        return result, quality

    def _generate_sources(
        self,
        func_name: str,
        signature: List[str],
        output_fields: List[Dict],
        category: str,
        module_path: str = "",
    ) -> List[Dict]:
        """生成 sources 配置"""
        source_name = self._guess_source_name(func_name, module_path)

        input_mapping = {}
        for param in signature:
            input_mapping[param] = param

        output_mapping, mapping_quality = self._build_output_mapping(output_fields)

        param_transforms = self.param_transform_rules.infer(signature, category)

        source_entry = {
            "name": source_name,
            "func": func_name,
            "enabled": True,
            "input_mapping": input_mapping,
            "param_transforms": param_transforms,
            "output_mapping": output_mapping,
        }

        # 根据映射质量添加不同的 TODO 注释
        if mapping_quality == "empty":
            source_entry["# TODO_note"] = "⚠️ 无输出字段，需手动补充 output_mapping"
        elif mapping_quality == "partial":
            source_entry["# TODO_note"] = "⚠️ 部分字段未映射，请审核 output_mapping 是否正确"
        else:
            source_entry["# TODO_note"] = "请审核 output_mapping 和 param_transforms 是否正确"

        return [source_entry]

    def _build_output_mapping(self, output_fields: List[Dict]) -> tuple:
        """构建 output_mapping

        Returns:
            tuple: (mapping_dict, quality)
        """
        if not output_fields:
            return {}, "empty"

        # 噪声字段模式（与 _generate_output 保持一致）
        noise_patterns = {
            '_', '-', '[', ']', '{', '}', '(', ')', '*', '+', '=', '/', '\\',
            ':', ';', ',', '.', '!', '?', '#', '@', '$', '%', '^', '&', '~',
            '`', '|', '"', "'", '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'f', 's', 'u', 'v', 'c', 'p', 'n', 't', 'd', 'a', 'b', 'o', 'h', 'l',
            'result', 'results', 'data', 'df', 'ret', 'col', 'ms', 'zf', 'in', 'if',
        }

        mapping = {}
        mapped_count = 0
        total_count = 0

        for field in output_fields:
            source_col = field["name"]

            # 过滤噪声字段
            if source_col.lower() in noise_patterns:
                continue

            if len(source_col) <= 2 and not any('\u4e00' <= c <= '\u9fff' for c in source_col):
                if source_col.lower() not in {'date', 'open', 'high', 'low', 'close', 'pe', 'pb', 'nav', 'code', 'name', 'price', 'bid1', 'ask1', 'id', 'ip'}:
                    continue

            total_count += 1
            target_col = self.name_normalizer.normalize(source_col)
            mapping[source_col] = target_col
            if source_col != target_col:
                mapped_count += 1

        # 计算质量
        if total_count == 0:
            quality = "empty"
        elif mapped_count == total_count:
            quality = "complete"
        elif mapped_count > 0:
            quality = "partial"
        else:
            quality = "empty"

        return mapping, quality

    def _guess_source_name(self, func_name: str, module_path: str = "") -> str:
        """猜测数据源名称

        优先级:
        1. 模块路径精确匹配 (_MODULE_SOURCE_MAP)
        2. 函数名后缀匹配 (_sina, _em, _ths 等)
        3. 函数名前缀匹配 (_source_prefix_map)
        4. 默认返回 akshare_em
        """
        # 1. 优先检查模块路径
        if module_path and module_path in _MODULE_SOURCE_MAP:
            return _MODULE_SOURCE_MAP[module_path]

        # 2. 检查函数名后缀
        func_lower = func_name.lower()
        if func_lower.endswith("_sina"):
            return "akshare_sina"
        if func_lower.endswith("_em"):
            return "akshare_em"
        if func_lower.endswith("_ths"):
            return "akshare_ths"
        if func_lower.endswith("_cninfo"):
            return "akshare_cninfo"
        if func_lower.endswith("_cn"):
            return "akshare_cn"
        if func_lower.endswith("_xq"):
            return "akshare_xq"
        if func_lower.endswith("_baidu"):
            return "akshare_baidu"
        if func_lower.endswith("_cx"):
            return "akshare_cx"

        # 3. 检查函数名前缀
        for prefix, source in self._source_prefix_map.items():
            if func_name.startswith(prefix):
                return source

        return "akshare_em"

    def _infer_param_type(self, param_name: str) -> str:
        """推断参数类型"""
        date_patterns = ["date", "start", "end", "time", "month", "year"]
        if any(p in param_name.lower() for p in date_patterns):
            return "str"

        float_patterns = ["price", "rate", "ratio", "pct", "amount", "volume"]
        if any(p in param_name.lower() for p in float_patterns):
            return "float"

        int_patterns = ["limit", "count", "page", "size", "num"]
        if any(p in param_name.lower() for p in int_patterns):
            return "int"

        if param_name.lower() in ["symbol", "code", "stock", "fund"]:
            return "str"

        if param_name.lower() in ["adjust", "period", "type", "status"]:
            return "str"

        return "str"

    def _truncate_description(self, desc: str, max_len: int = 200) -> str:
        """截断过长的描述"""
        if not desc:
            return ""
        if len(desc) <= max_len:
            return desc
        return desc[:max_len] + "..."

    def generate_all(
        self,
        registry: Dict[str, Any],
        output_dir: Path,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """生成所有 interface skeletons"""
        output_dir.mkdir(parents=True, exist_ok=True)
        interfaces = registry.get("interfaces", {})
        by_category: Dict[str, List] = {}

        for name, entry in interfaces.items():
            category = entry.get("category", "other")
            if categories and category not in categories:
                continue

            skeleton = self.generate(entry)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, skeleton))

        output_files = {}
        for category, entries in by_category.items():
            output_file = output_dir / f"{category}_skeleton.yaml"
            import yaml
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump({name: entry for name, entry in entries}, f, default_flow_style=False, allow_unicode=True)
            output_files[category] = output_file
            logger.info(f"Generated {len(entries)} skeletons for category '{category}' to {output_file}")

        # 打印质量报告
        self._print_quality_report()

        return output_files

    def _print_quality_report(self):
        """打印生成质量报告"""
        stats = self._stats
        total = stats["total_interfaces"]
        if total == 0:
            logger.info("No interfaces generated.")
            return

        with_output = stats["with_output_fields"]
        complete = stats["with_complete_mapping"]
        partial = stats["with_partial_mapping"]
        empty = stats["with_empty_mapping"]

        report = f"""
生成质量报告:
{'='*50}
  总接口数:           {total}
  有输出字段:         {with_output} ({with_output/total*100:.1f}%)
  - 完整映射:         {complete} ({complete/max(with_output,1)*100:.1f}%)
  - 部分映射:         {partial} ({partial/max(with_output,1)*100:.1f}%)
  - 空映射:           {empty} ({empty/max(with_output,1)*100:.1f}%)

  Source 分布:
"""
        for source, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
            report += f"    {source:20s} {count:5d} ({count/total*100:.1f}%)\n"

        report += f"""
  Category 分布:
"""
        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            report += f"    {cat:20s} {count:5d} ({count/total*100:.1f}%)\n"

        report += f"{'='*50}"
        logger.info(report)

    def get_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return self._stats.copy()

        return output_files