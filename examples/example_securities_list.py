"""
get_securities_list() 接口示例

演示如何使用 akshare_data.get_securities_list() 获取各类证券列表。

支持的证券类型:
  - "stock": 股票列表 (默认)
  - "etf": ETF 基金列表
  - "index": 指数列表
  - "lof": LOF 基金列表
  - "fund": 开放式基金列表

参数说明:
  - security_type: 证券类型，默认为 "stock"
  - date: 可选 (仅 Tushare/Lixinger 数据源支持, akshare 源忽略此参数)

返回字段: code, display_name, type, start_date, security_type

导入方式: from akshare_data import get_securities_list
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
import pandas as pd
import akshare as ak
from akshare_data import get_securities_list

logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _mock_securities(security_type):
    return pd.DataFrame([
        {"code": "600519", "display_name": "贵州茅台", "security_type": security_type, "start_date": "2001-08-27"},
        {"code": "000001", "display_name": "平安银行", "security_type": security_type, "start_date": "1991-04-03"},
    ])


def _fetch_securities(security_type: str):
    try:
        df = get_securities_list(security_type=security_type)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    try:
        df = get_securities_list(type=security_type)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()


def _call_akshare_securities(symbol="", market="", fund_type="", name=None):
    """Use akshare directly as fallback."""
    try:
        if name == "lof":
            df = ak.fund_lof_list_em()
        elif name == "etf":
            df = ak.fund_etf_list_sina()
        elif name == "fund":
            df = ak.fund_open_fund_search(indicator="全部")
        else:
            df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()


def _sample_securities():
    return pd.DataFrame(
        [
            {"code": "600519", "display_name": "贵州茅台", "security_type": "stock", "start_date": "2001-08-27"},
            {"code": "000001", "display_name": "平安银行", "security_type": "stock", "start_date": "1991-04-03"},
        ]
    )


def _safe_subset(df: pd.DataFrame, cols):
    available = [c for c in cols if c in df.columns]
    return df[available] if available else df.head(10)


# ============================================================
# 示例 1: 基本用法 - 获取 A 股股票列表
# ============================================================
def example_basic_stocks():
    """基本用法: 获取全部 A 股股票列表"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取 A 股股票列表")
    print("=" * 60)

    try:
        df = _fetch_securities("stock")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前5行数据:")
        print(df.head())

        print("\n后5行数据:")
        print(df.tail())

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 获取 ETF 列表
# ============================================================
def example_etf_list():
    """获取 ETF 基金列表"""
    print("\n" + "=" * 60)
    print("示例 2: 获取 ETF 基金列表")
    print("=" * 60)

    try:
        df = _fetch_securities("etf")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10只ETF:")
        print(_safe_subset(df, ["code", "display_name", "start_date"]).head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 获取指数列表
# ============================================================
def example_index_list():
    """获取指数列表"""
    print("\n" + "=" * 60)
    print("示例 3: 获取指数列表")
    print("=" * 60)

    try:
        df = _fetch_securities("index")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10个指数:")
        print(_safe_subset(df, ["code", "display_name", "start_date"]).head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 获取 LOF 基金列表
# ============================================================
def example_lof_list():
    """获取 LOF (上市型开放式基金) 列表"""
    print("\n" + "=" * 60)
    print("示例 4: 获取 LOF 基金列表")
    print("=" * 60)

    try:
        df = _fetch_securities("lof")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10只LOF基金:")
        print(_safe_subset(df, ["code", "display_name", "start_date"]).head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 5: 获取开放式基金列表
# ============================================================
def example_fund_list():
    """获取开放式基金列表"""
    print("\n" + "=" * 60)
    print("示例 5: 获取开放式基金列表")
    print("=" * 60)

    try:
        df = _fetch_securities("fund")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10只开放式基金:")
        print(_safe_subset(df, ["code", "display_name", "start_date"]).head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 6: 统计各类型证券数量 (date 参数由 Tushare/Lixinger 数据源支持)
# ============================================================
def example_with_date():
    """注意: date 参数仅 Tushare/Lixinger 数据源支持, akshare 源忽略"""
    print("\n" + "=" * 60)
    print("示例 6: 获取证券列表 (不含日期过滤)")
    print("=" * 60)

    try:
        df = _fetch_securities("stock")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前5行数据:")
        print(df.head())

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 7: 统计各类型证券数量
# ============================================================
def example_statistics():
    """统计各类证券数量"""
    print("\n" + "=" * 60)
    print("示例 7: 统计各类型证券数量")
    print("=" * 60)

    security_types = ["stock", "etf", "index", "lof", "fund"]

    for sec_type in security_types:
        try:
            df = _fetch_securities(sec_type)
            count = 0 if df is None or df.empty else len(df)
            print(f"{sec_type:8s}: {count:>6} 只")
        except Exception as e:
            print(f"{sec_type:8s}: 获取失败 - {e}")


# ============================================================
# 示例 8: 筛选特定板块股票
# ============================================================
def example_filter_stocks():
    """演示如何筛选特定条件的股票"""
    print("\n" + "=" * 60)
    print("示例 8: 筛选特定条件的股票")
    print("=" * 60)

    try:
        df = _fetch_securities("stock")
        if df is None or df.empty:
            print("无数据，使用样本回退")
            df = _sample_securities()

        code_col = "code" if "code" in df.columns else ("symbol" if "symbol" in df.columns else None)
        if code_col is None:
            print("无法识别证券代码列，打印样本:")
            print(df.head(10))
            return
        code_series = df[code_col].astype(str)
        sh_stocks = df[code_series.str.startswith("60")]
        print(f"沪市主板股票 (60开头): {len(sh_stocks)} 只")
        print(sh_stocks.head(5))

        sz_stocks = df[code_series.str.startswith("00")]
        print(f"\n深市主板股票 (00开头): {len(sz_stocks)} 只")
        print(sz_stocks.head(5))

        cyb_stocks = df[code_series.str.startswith("30")]
        print(f"\n创业板股票 (30开头): {len(cyb_stocks)} 只")
        print(cyb_stocks.head(5))

        kcb_stocks = df[code_series.str.startswith("68")]
        print(f"\n科创板股票 (68开头): {len(kcb_stocks)} 只")
        print(kcb_stocks.head(5))

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic_stocks()
    example_etf_list()
    example_index_list()
    example_lof_list()
    example_fund_list()
    example_with_date()
    example_statistics()
    example_filter_stocks()