"""
get_ipo_info() 接口示例

演示如何使用 akshare_data.get_ipo_info() 获取新股IPO信息。

注意: ipo_info 接口当前未在 equity.yaml 中配置，此功能可能不可用。
如需新股数据，请使用 get_new_stocks() 接口 (对应 stock_xgsglb_em)。

返回字段: 包含股票代码、名称、发行价、市盈率、申购日期等信息
"""

import pandas as pd
from akshare_data import get_service
from _example_utils import first_non_empty_by_symbol, stable_df


def _rename_by_aliases(df: pd.DataFrame, alias_map: dict[str, list[str]]) -> pd.DataFrame:
    renamed = df.copy()
    for target, aliases in alias_map.items():
        if target in renamed.columns:
            continue
        for alias in aliases:
            if alias in renamed.columns:
                renamed = renamed.rename(columns={alias: target})
                break
    return renamed


def _recent_listing_symbols(service, limit: int = 12) -> list[str]:
    try:
        securities = service.get_securities_list(security_type="stock")
    except Exception:
        return []
    if securities is None or securities.empty:
        return []

    securities = _rename_by_aliases(
        securities,
        {
            "symbol": ["代码", "证券代码", "code"],
            "list_date": ["上市日期", "上市时间", "ipo_date"],
        },
    )
    if "symbol" not in securities.columns:
        return []

    data = securities.copy()
    if "list_date" in data.columns:
        data["list_date"] = pd.to_datetime(data["list_date"], errors="coerce")
        data = data.sort_values("list_date", ascending=False)
    symbols = data["symbol"].dropna().astype(str).drop_duplicates()
    return symbols.head(limit).tolist()


def _fallback_by_recent_symbols(service) -> tuple[pd.DataFrame, str | None]:
    symbols = _recent_listing_symbols(service, limit=15)
    if not symbols:
        return pd.DataFrame(), None

    def _fetch_daily(symbol: str) -> pd.DataFrame:
        return service.get_daily(symbol=symbol, start_date="2025-01-01", end_date="2026-12-31")

    df, hit_symbol = first_non_empty_by_symbol(_fetch_daily, symbols)
    if df is None or df.empty:
        return pd.DataFrame(), None
    view = stable_df(df).head(20).copy()
    view.insert(0, "fallback_symbol", hit_symbol)
    return view, hit_symbol


def _fetch_ipo_df(service):
    """优先 IPO 表，空数据时回退新股申购表，再回退近期上市 symbol 探测。"""
    for name, func in (("ipo_info", service.get_ipo_info), ("new_stocks", service.get_new_stocks)):
        try:
            df = func()
            if df is not None and not df.empty:
                cleaned = _rename_by_aliases(
                    stable_df(df),
                    {
                        "symbol": ["代码", "证券代码", "code"],
                        "name": ["名称", "证券简称", "股票简称"],
                        "issue_price": ["发行价", "发行价格"],
                        "pe_ratio": ["市盈率", "发行市盈率", "PE"],
                        "申购日期": ["申购日", "申购时间", "网上申购日"],
                    },
                )
                return cleaned, name
        except Exception:
            continue
    fallback_df, hit_symbol = _fallback_by_recent_symbols(service)
    if fallback_df is not None and not fallback_df.empty:
        return fallback_df, f"daily_by_recent_symbol({hit_symbol})"
    return pd.DataFrame(), None


def _show_sample_ipo():
    sample = pd.DataFrame(
        [
            {"symbol": "301000", "name": "示例科技", "issue_price": 18.5, "pe_ratio": 22.3, "申购日期": "2024-06-10"},
            {"symbol": "603000", "name": "示例制造", "issue_price": 25.8, "pe_ratio": 19.7, "申购日期": "2024-07-03"},
        ]
    )
    print("使用本地样本数据回退:")
    print(sample.to_string(index=False))


# ============================================================
# 示例 1: 基本用法 - 获取最新IPO信息
# ============================================================
def example_basic():
    """基本用法: 获取最新新股IPO信息"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取最新新股IPO信息")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_ipo_df(service)
        if df is None or df.empty:
            print("无数据，切换样本回退")
            _show_sample_ipo()
            return

        print(f"命中来源: {source_name}")
        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10条IPO信息:")
        print(df.head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 筛选特定字段
# ============================================================
def example_filter_fields():
    """演示如何筛选感兴趣的字段"""
    print("\n" + "=" * 60)
    print("示例 2: 筛选特定字段")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_ipo_df(service)
        if df is None or df.empty:
            print("无数据，切换样本回退")
            _show_sample_ipo()
            return

        print(f"命中来源: {source_name}")
        interest_cols = ["symbol", "name", "issue_price", "pe_ratio", "申购日期"]
        available = [c for c in interest_cols if c in df.columns]

        if available:
            print(f"可用字段: {available}")
            print(df[available].head(10))
        else:
            print(f"所有字段: {list(df.columns)}")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 统计IPO数据
# ============================================================
def example_statistics():
    """对新股IPO数据进行统计分析"""
    print("\n" + "=" * 60)
    print("示例 3: IPO数据统计分析")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_ipo_df(service)
        if df is None or df.empty:
            print("无数据，切换样本回退")
            _show_sample_ipo()
            return

        print(f"命中来源: {source_name}")
        print(f"共 {len(df)} 只新股")

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            print("\n数值字段统计:")
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_filter_fields()
    example_statistics()
