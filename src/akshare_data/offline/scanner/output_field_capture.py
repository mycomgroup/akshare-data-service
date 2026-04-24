"""输出字段捕获器 - 捕获函数返回的列信息"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Set

import pandas as pd

from akshare_data.offline.scanner.column_type_inferrer import ColumnTypeInferrer
from akshare_data.offline.scanner.code_parser import CodeParser

logger = logging.getLogger("akshare_data")

DEFAULT_TIMEOUT_SECONDS = 10

PROXY_URL = "http://127.0.0.1:7897"

PROXY_FUNC_PREFIXES = [
    "article_",
    "fred_",
    "macro_usa_",
    "macro_uk_",
    "macro_china_",
    "macro_bank_",
    "macro_germany_",
    "macro_japan_",
    "macro_swiss_",
    "macro_shipping_",
    "stock_hk_",
    "stock_financial_",
    "stock_lh_",
    "stock_js_",
    "stock_zyjs_",
    "stock_sgt_",
    "stock_ipo_",
    "stock_info_",
    "stock_profit_",
    "stock_board_",
    "stock_classify_",
    "stock_comment_",
    "stock_individual_",
    "stock_lhb_",
    "stock_notice_",
    "stock_repurchase_",
    "stock_sector_",
    "stock_us_",
    "stock_a_congestion_",
    "stock_a_high_",
    "option_cffex_",
    "option_sse_",
    "option_current_",
    "option_comm_",
    "option_contract_",
    "option_hist_",
    "option_margin_",
    "option_risk_",
    "air_quality_",
    "fund_aum_",
    "fund_balance_",
    "fund_linghuo_",
    "fund_overview_",
    "fund_stock_",
    "futures_delivery_",
    "futures_display_",
    "futures_fees_",
    "futures_gfex_",
    "futures_hold_",
    "futures_rule_",
    "futures_settle_",
    "futures_settlement_",
    "futures_spot_",
    "futures_to_",
    "futures_warehouse_",
    "futures_zh_",
    "get_czce_",
    "get_futures_",
    "get_gfex_",
    "get_ine_",
    "get_rank_",
    "get_receipt_",
    "get_roll_",
    "match_main_",
    "index_bloomberg_",
    "index_csindex_",
    "index_detail_",
    "index_eri_",
    "index_stock_",
    "index_us_",
    "bond_china_yield",
    "bond_zh_hs_",
    "qhkc_tool_",
    "nlp_answer",
    "news_cctv",
    "migration_area_",
    "fred_md",
    "fred_qd",
    "currency_currencies",
    "energy_carbon_",
    "car_market_",
    "car_sale_",
    "sw_index_",
    "stock_zh_a_daily",
    "stock_zh_a_hist_min_em",
    "stock_zh_a_hist_pre_min_em",
    "stock_zh_a_cdr_daily",
    "stock_zh_a_minute",
    "stock_zh_a_disclosure_relation_cninfo",
    "stock_zh_a_disclosure_report_cninfo",
    "stock_zh_b_daily",
    "stock_zh_b_minute",
    "stock_zh_index_daily",
    "stock_zh_index_daily_em",
    "stock_zh_index_daily_tx",
    "stock_zh_index_spot_em",
    "stock_zh_index_value_csindex",
    "stock_zh_kcb_daily",
    "stock_zh_dupont_comparison_em",
    "stock_zh_growth_comparison_em",
    "stock_zh_scale_comparison_em",
    "stock_zh_valuation_baidu",
    "stock_zh_valuation_comparison_em",
]

TIMEOUT_BY_PREFIX = {
    "article_": 30,
    "fred_": 30,
    "forbes_": 30,
    "bond_china_yield": 30,
    "bond_zh_hs_cov_": 15,
    "currency_pair_map": 30,
    "currency_currencies": 30,
    "energy_carbon_": 30,
    "index_bloomberg_": 30,
    "index_csindex_": 15,
    "index_stock_cons": 30,
    "futures_foreign_": 15,
    "futures_shfe_warehouse_receipt": 15,
    "bond_cb_index_jsl": 15,
    "fund_etf_spot_ths": 10,
    "macro_usa_": 20,
    "macro_uk_": 20,
    "macro_china_": 20,
    "macro_bank_": 20,
    "macro_germany_": 20,
    "macro_japan_": 20,
    "macro_swiss_": 20,
    "macro_shipping_": 20,
    "stock_hk_": 15,
    "stock_financial_": 15,
    "stock_lh_": 15,
    "stock_js_": 15,
    "stock_sgt_": 15,
    "stock_ipo_": 15,
    "stock_info_": 15,
    "stock_profit_": 15,
    "stock_board_": 15,
    "stock_us_": 15,
    "option_cffex_": 15,
    "option_sse_": 15,
    "option_current_": 15,
    "option_comm_": 15,
    "option_contract_": 15,
    "option_hist_": 15,
    "option_margin_": 15,
    "option_risk_": 15,
    "air_quality_": 20,
    "fund_aum_": 15,
    "fund_balance_": 15,
    "fund_linghuo_": 15,
    "fund_overview_": 15,
    "fund_stock_": 15,
    "futures_delivery_": 15,
    "futures_display_": 15,
    "futures_fees_": 15,
    "futures_gfex_": 15,
    "futures_hold_": 15,
    "futures_rule_": 15,
    "futures_settle_": 15,
    "futures_settlement_": 15,
    "futures_spot_": 15,
    "futures_to_": 15,
    "futures_warehouse_": 15,
    "futures_zh_": 15,
    "get_czce_": 15,
    "get_futures_": 15,
    "get_gfex_": 15,
    "get_ine_": 15,
    "get_rank_": 15,
    "get_receipt_": 15,
    "get_roll_": 15,
    "match_main_": 15,
    "index_bloomberg_": 30,
    "index_csindex_": 15,
    "index_detail_": 15,
    "index_eri_": 15,
    "index_stock_": 30,
    "index_us_": 15,
    "bond_china_yield": 30,
    "bond_zh_hs_": 15,
    "qhkc_tool_": 15,
    "fred_md": 30,
    "fred_qd": 30,
    "currency_currencies": 30,
    "energy_carbon_": 30,
    "car_market_": 15,
    "car_sale_": 15,
    "migration_area_": 20,
    "stock_zh_a_hist_min_em": 15,
    "stock_zh_a_hist_pre_min_em": 15,
    "stock_zh_a_minute": 15,
    "stock_hk_hist_min_em": 15,
    "stock_us_hist_min_em": 15,
    "fund_etf_hist_min_em": 15,
    "fund_lof_hist_min_em": 15,
}

SPECIAL_SYMBOL_FUNCS = {
    "air_quality_hist": "day",
    "amac_person_fund_org_list": "公募基金管理公司",
    "article_epu_index": "China",
    "article_oman_rv": "FTSE",
    "article_oman_rv_short": "FTSE",
    "bank_fjcf_table_detail": "分局本级",
    "bond_cb_profile_sina": "sz128039",
    "bond_cb_summary_sina": "sh155255",
    "bond_gb_us_sina": "美国10年期国债",
    "bond_gb_zh_sina": "中国10年期国债",
    "bond_index_general_cbond": "新综合指数",
    "bond_info_cm_query": "评级等级",
    "bond_info_detail_cm": "淮安农商行CDSD2022021012",
    "bond_zh_cov_info": "基本信息",
    "bond_zh_hs_cov_daily": "sh010107",
    "bond_zh_hs_cov_min": "sz128039",
    "bond_zh_hs_cov_pre_min": "sh113570",
    "bond_zh_hs_daily": "sh010107",
    "car_market_fuel_cpca": "整体市场",
    "car_market_man_rank_cpca": "狭义乘用车-单月",
    "car_market_total_cpca": "狭义乘用车",
    "car_sale_rank_gasgoo": "车企榜",
    "currency_convert": "USD",
    "currency_currencies": "fiat",
    "currency_history": "USD",
    "currency_latest": "USD",
    "currency_time_series": "USD",
    "drewry_wci_index": "composite",
    "forex_hist_em": "USDCNH",
    "fund_cf_em": "FSRQ",
    "fund_etf_category_sina": "LOF基金",
    "fund_etf_category_ths": "ETF",
    "fund_etf_dividend_sina": "sh510050",
    "fund_etf_hist_sina": "sh510050",
    "fund_fee_em": "认购费率",
    "fund_fh_em": "BZDM",
    "fund_hk_fund_hist_em": "历史净值明细",
    "fund_info_index_em": "沪深指数",
    "fund_open_fund_info_em": "单位净值走势",
    "fund_portfolio_change_em": "累计买入",
    "fund_scale_daily_szse": "ETF",
    "fund_scale_open_sina": "股票型基金",
    "futures_contract_detail": "AP2101",
    "futures_contract_detail_em": "v2602F",
    "futures_foreign_detail": "ZSD",
    "futures_foreign_hist": "ZSD",
    "futures_global_hist_em": "HG00Y",
    "futures_hist_em": "热卷主连",
    "futures_hog_core": "外三元",
    "futures_hog_supply": "猪肉批发价",
    "futures_hold_pos_sina": "成交量",
    "futures_index_ccidx": "中证商品期货指数",
    "futures_settle": "CFFEX",
    "futures_spot_sys": "市场价格",
    "futures_zh_daily_sina": "RB0",
    "futures_zh_minute_sina": "IF2008",
    "futures_zh_realtime": "PTA",
    "futures_zh_spot": "V2309",
    "fx_quote_baidu": "人民币",
    "get_futures_daily": "CFFEX",
    "get_roll_yield_bar": "var",
    "hurun_rank": "胡润百富榜",
    "index_analysis_daily_sw": "市场表征",
    "index_analysis_monthly_sw": "市场表征",
    "index_analysis_week_month_sw": "month",
    "index_analysis_weekly_sw": "市场表征",
    "index_global_hist_em": "美元指数",
    "index_global_hist_sina": "OMX",
    "index_hist_fund_sw": "day",
    "index_hist_sw": "day",
    "index_kq_fashion": "时尚创意指数",
    "index_kq_fz": "价格指数",
    "index_price_cflp": "周指数",
    "index_realtime_fund_sw": "基础一级",
    "index_realtime_sw": "二级行业",
    "index_us_stock_sina": ".INX",
    "index_volume_cflp": "月指数",
    "index_yw": "月景气指数",
    "macro_china_nbs_nation": "LAST10",
    "macro_china_nbs_region": "LAST10",
    "match_main_contract": "cffex",
    "migration_area_baidu": "重庆市",
    "migration_scale_baidu": "广州市",
    "nlp_answer": "人工智能",
    "nlp_ownthink": "人工智能",
    "option_cffex_hs300_daily_sina": "io2202P4350",
    "option_cffex_hs300_spot_sina": "io2204",
    "option_cffex_sz50_daily_sina": "ho2303P2350",
    "option_cffex_sz50_spot_sina": "ho2303",
    "option_cffex_zz1000_daily_sina": "mo2208P6200",
    "option_cffex_zz1000_spot_sina": "mo2208",
    "option_comm_info": "工业硅期权",
    "option_commodity_contract_sina": "玉米期权",
    "option_commodity_contract_table_sina": "黄金期权",
    "option_commodity_hist_sina": "au2012C392",
    "option_finance_board": "嘉实沪深300ETF期权",
    "option_finance_sse_underlying": "华夏科创50ETF期权",
    "option_hist_czce": "白糖期权",
    "option_hist_dce": "聚丙烯期权",
    "option_hist_gfex": "工业硅",
    "option_hist_shfe": "铝期权",
    "option_lhb_em": "期权交易情况-认沽交易量",
    "option_margin": "原油期权",
    "option_minute_em": "MO2404-P-4450",
    "option_sse_codes_sina": "看涨期权",
    "option_sse_expire_day_sina": "50ETF",
    "option_sse_list_sina": "50ETF",
    "option_sse_underlying_spot_price_sina": "sh510300",
    "option_vol_gfex": "碳酸锂",
    "option_vol_shfe": "铝期权",
    "rate_interbank": "上海银行同业拆借市场",
    "repo_rate_query": "回购定盘利率",
    "rv_from_futures_zh_minute_sina": "IF2008",
    "rv_from_stock_zh_a_hist_min_em": "hfq",
    "spot_goods": "波罗的海干散货指数",
    "spot_hist_sge": "Au99.99",
    "spot_price_qh": "螺纹钢",
    "spot_quotations_sge": "Au99.99",
    "stock_a_below_net_asset_statistics": "全部A股",
    "stock_a_gxl_lg": "上证A股",
    "stock_a_high_low_statistics": "all",
    "stock_analyst_detail_em": "最新跟踪成分股",
    "stock_balance_sheet_by_report_delisted_em": "SZ000013",
    "stock_balance_sheet_by_report_em": "SH600519",
    "stock_balance_sheet_by_yearly_em": "SH600036",
    "stock_board_concept_cons_em": "融资融券",
    "stock_board_concept_hist_em": "绿色电力",
    "stock_board_concept_hist_min_em": "长寿药",
    "stock_board_concept_index_ths": "阿里巴巴概念",
    "stock_board_concept_info_ths": "阿里巴巴概念",
    "stock_board_concept_spot_em": "可燃冰",
    "stock_board_industry_cons_em": "小金属",
    "stock_board_industry_hist_em": "小金属",
    "stock_board_industry_hist_min_em": "小金属",
    "stock_board_industry_info_ths": "半导体",
    "stock_board_industry_spot_em": "小金属",
    "stock_cash_flow_sheet_by_quarterly_em": "SH600519",
    "stock_cash_flow_sheet_by_report_delisted_em": "SZ000013",
    "stock_cash_flow_sheet_by_report_em": "SH600519",
    "stock_cash_flow_sheet_by_yearly_em": "SH600519",
    "stock_changes_em": "大笔买入",
    "stock_classify_sina": "热门概念",
    "stock_concept_cons_futu": "特朗普概念股",
    "stock_concept_fund_flow_hist": "数据要素",
    "stock_dzjy_hygtj": "近三月",
    "stock_dzjy_hyyybtj": "近3日",
    "stock_dzjy_yybph": "近三月",
    "stock_financial_abstract_new_ths": "按报告期",
    "stock_financial_abstract_ths": "按报告期",
    "stock_financial_analysis_indicator_em": "301389.SZ",
    "stock_financial_benefit_new_ths": "按报告期",
    "stock_financial_benefit_ths": "按报告期",
    "stock_financial_cash_new_ths": "按报告期",
    "stock_financial_cash_ths": "按报告期",
    "stock_financial_debt_new_ths": "按报告期",
    "stock_financial_debt_ths": "按报告期",
    "stock_financial_hk_report_em": "资产负债表",
    "stock_financial_report_sina": "sh600600",
    "stock_financial_us_analysis_indicator_em": "TSLA",
    "stock_financial_us_report_em": "TSLA",
    "stock_gdfx_free_top_10_em": "sh688686",
    "stock_gdfx_top_10_em": "sh688686",
    "stock_hk_index_daily_em": "HSTECF2L",
    "stock_hk_index_daily_sina": "CES100",
    "stock_hk_indicator_eniu": "hk01093",
    "stock_hk_profit_forecast_et": "盈利预测概览",
    "stock_hk_valuation_baidu": "总市值",
    "stock_hot_deal_xq": "最热门",
    "stock_hot_follow_xq": "最热门",
    "stock_hot_keyword_em": "SZ000665",
    "stock_hot_rank_detail_em": "SZ000665",
    "stock_hot_rank_detail_realtime_em": "SZ000665",
    "stock_hot_rank_latest_em": "SZ000665",
    "stock_hot_rank_relate_em": "SZ000665",
    "stock_hot_tweet_xq": "最热门",
    "stock_hsgt_board_rank_em": "北向资金增持行业板块排行",
    "stock_hsgt_fund_min_em": "北向资金",
    "stock_hsgt_hist_em": "北向资金",
    "stock_hsgt_hold_stock_em": "沪股通",
    "stock_hsgt_institution_statistics_em": "北向持股",
    "stock_hsgt_stock_statistics_em": "北向持股",
    "stock_index_pb_lg": "上证50",
    "stock_index_pe_lg": "沪深300",
    "stock_individual_basic_info_us_xq": "NVDA",
    "stock_individual_basic_info_xq": "SH601127",
    "stock_individual_spot_xq": "SH600000",
    "stock_industry_category_cninfo": "巨潮行业分类标准",
    "stock_industry_pe_ratio_cninfo": "证监会行业分类",
    "stock_info_sh_name_code": "主板A股",
    "stock_info_sz_change_name": "全称变更",
    "stock_info_sz_delist": "终止上市公司",
    "stock_info_sz_name_code": "A股列表",
    "stock_institute_recommend": "投资评级选股",
    "stock_intraday_sina": "sz000001",
    "stock_ipo_ths": "全部A股",
    "stock_js_weibo_report": "CNHOUR12",
    "stock_lhb_jgstatistic_em": "近一月",
    "stock_lhb_stock_statistic_em": "近一月",
    "stock_lhb_traderstatistic_em": "近一月",
    "stock_lhb_yybph_em": "近一月",
    "stock_main_fund_flow": "全部股票",
    "stock_profit_forecast_ths": "预测年报每股收益",
    "stock_profit_sheet_by_quarterly_em": "SH600519",
    "stock_profit_sheet_by_report_delisted_em": "SZ000013",
    "stock_profit_sheet_by_report_em": "SH600519",
    "stock_profit_sheet_by_yearly_em": "SH600519",
    "stock_rank_cxd_ths": "创月新低",
    "stock_rank_cxg_ths": "创月新高",
    "stock_rank_xstp_ths": "500日均线",
    "stock_rank_xxtp_ths": "500日均线",
    "stock_report_disclosure": "沪深京",
    "stock_report_fund_hold": "基金持仓",
    "stock_restricted_release_summary_em": "全部股票",
    "stock_sector_detail": "gn_gfgn",
    "stock_sector_fund_flow_hist": "汽车服务",
    "stock_sector_fund_flow_rank": "行业资金流",
    "stock_sector_fund_flow_summary": "电源设备",
    "stock_sector_spot": "新浪行业",
    "stock_us_famous_spot_em": "科技类",
    "stock_us_hist": "105.MSFT",
    "stock_us_valuation_baidu": "NVDA",
    "stock_xgsglb_em": "全部股票",
    "stock_yysj_em": "沪深A股",
    "stock_zh_a_cdr_daily": "sh689009",
    "stock_zh_a_daily": "sh603843",
    "stock_zh_a_disclosure_relation_cninfo": "沪深京",
    "stock_zh_a_disclosure_report_cninfo": "沪深京",
    "stock_zh_a_gbjg_em": "603392.SH",
    "stock_zh_a_hist_min_em": "sh600519",
    "stock_zh_a_hist_pre_min_em": "sh600519",
    "stock_zh_a_hist_tx": "sz000001",
    "stock_zh_a_minute": "sh600519",
    "stock_zh_a_tick_tx_js": "sz000001",
    "stock_zh_b_daily": "sh900901",
    "stock_zh_b_minute": "sh900901",
    "stock_zh_dupont_comparison_em": "SZ000895",
    "stock_zh_growth_comparison_em": "SZ000895",
    "stock_zh_index_daily": "sh000922",
    "stock_zh_index_daily_em": "csi931151",
    "stock_zh_index_daily_tx": "sz980017",
    "stock_zh_index_spot_em": "上证系列指数",
    "stock_zh_index_value_csindex": "H30374",
    "stock_zh_kcb_daily": "sh688399",
    "stock_zh_scale_comparison_em": "SZ000895",
    "stock_zh_valuation_baidu": "总市值",
    "stock_zh_valuation_comparison_em": "SZ000895",
    "stock_zygc_em": "SH688041",
    "sunrise_daily": "beijing",
    "sunrise_monthly": "beijing",
    "sw_index_third_cons": "801120.SI",
}

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
    name: str
    inferred_type: str = "str"
    source: str = "unknown"
    description: str = ""


class OutputFieldCapture:
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

    def _should_use_proxy(self, func_name: str) -> bool:
        for prefix in PROXY_FUNC_PREFIXES:
            if func_name.startswith(prefix):
                return True
        return False

    def _setup_proxy(self):
        os.environ["HTTP_PROXY"] = PROXY_URL
        os.environ["HTTPS_PROXY"] = PROXY_URL
        os.environ["http_proxy"] = PROXY_URL
        os.environ["https_proxy"] = PROXY_URL

    def _clear_proxy(self):
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(key, None)

    def _suppress_output(self, func, *args, **kwargs):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        old_warnings_filters = warnings.filters[:]
        warnings.filterwarnings("ignore")
        try:
            result = func(*args, **kwargs)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            warnings.filters[:] = old_warnings_filters
        return result

    def get_timeout_for_func(self, func_name: str) -> int:
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
        if use_cache and func_name in self._failed_funcs:
            return []

        columns = self._capture_from_code(func_name, signature)
        if columns:
            return columns

        timeout = self.get_timeout_for_func(func_name)

        if self._should_use_proxy(func_name):
            self._setup_proxy()
            columns = self._capture_runtime(func_name, params, timeout)
            self._clear_proxy()
            if columns:
                return columns

        columns = self._capture_runtime(func_name, params, timeout)
        if columns:
            return columns

        self._failed_funcs.add(func_name)
        return []

    def get_stats(self) -> Dict[str, int]:
        return {
            **self._runtime_capture_stats,
            "failed_funcs": len(self._failed_funcs),
        }

    def _capture_from_code(self, func_name: str, signature: List[str]) -> List[OutputColumn]:
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
        func_obj = self._get_func_obj(func_name)
        if not func_obj:
            return []

        call_params = self._prepare_params(func_obj, params, func_name)
        if call_params is None:
            return []

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._suppress_output, func_obj, **call_params)
                result = future.result(timeout=timeout)

            if isinstance(result, pd.DataFrame):
                if result.empty:
                    self._runtime_capture_stats["failed"] += 1
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
        except FuturesTimeoutError:
            self._runtime_capture_stats["timeout"] += 1
        except Exception as e:
            self._runtime_capture_stats["failed"] += 1

        return []

    def _get_func_obj(self, func_name: str) -> Optional[Callable]:
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
        import inspect

        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            return None

        if func_name in NO_PARAM_FUNCS:
            return {}

        if func_name in SPECIAL_SYMBOL_FUNCS:
            special_value = SPECIAL_SYMBOL_FUNCS[func_name]
            if special_value:
                first_param_name = list(sig.parameters.keys())[0] if sig.parameters else None
                if first_param_name:
                    return {first_param_name: special_value}
            return {}

        call_params = {}
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
        if value is None:
            return False
        value_str = str(value)

        if len(value_str) > 200:
            return False

        if value_str.startswith(("http://", "https://")):
            return False

        if "&" in value_str and "=" in value_str:
            if not value_str.startswith("&"):
                return False

        invalid_chars = set("()/+^*[]{}")
        if any(c in invalid_chars for c in value_str):
            return False

        return True

    def _get_default_for_param(self, param_name: str, func_name: str) -> Optional[Any]:
        param_lower = param_name.lower()

        date_patterns = ["date", "start", "end", "time"]
        if any(p in param_lower for p in date_patterns):
            if "start" in param_lower:
                return (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            return datetime.now().strftime("%Y%m%d")

        if "symbol" in param_lower or "code" in param_lower or "stock" in param_lower:
            if "index" in func_name:
                return "000001"
            if "fund" in func_name:
                return "510300"
            return "000001"

        if "period" in param_lower:
            return "daily"

        if "adjust" in param_lower:
            return "qfq"

        if "market" in param_lower:
            return "sh"

        return None

    def _infer_df_column_type(self, series: pd.Series) -> str:
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