"""
get_repurchase_data() 接口示例

演示如何使用 akshare_data.get_repurchase_data() 获取股票回购数据。

返回字段: 包含股票代码、回购价格、回购数量、回购金额等。
"""

from akshare_data import get_service
from _example_utils import fetch_with_retry, normalize_symbol_input, print_df_brief, recent_trade_days, stable_df


def _fetch_repurchase_with_fallback(service):
    """稳健回退：日期窗口 -> 代码候选 -> 参数降级。"""
    symbol_candidates = []
    for raw in ("000001", "600000", "601318", "300750", "000333"):
        try:
            symbol_candidates.append(normalize_symbol_input(raw))
        except Exception:  # noqa: BLE001
            continue

    attempts = []
    for end_date in recent_trade_days(service, max_backtrack=8):
        start_year = f"{end_date[:4]}-01-01"
        attempts.append(("全市场+日期窗口", {"start_date": start_year, "end_date": end_date}))
        for symbol in symbol_candidates:
            attempts.append((
                f"代码+日期窗口(symbol={symbol}, start_date={start_year}, end_date={end_date})",
                {"symbol": symbol, "start_date": start_year, "end_date": end_date},
            ))

    for symbol in symbol_candidates:
        attempts.append((f"仅代码(symbol={symbol})", {"symbol": symbol}))

    attempts.append(("无参数", {}))

    for reason, kwargs in attempts:
        try:
            df = fetch_with_retry(
                lambda params=kwargs: service.get_repurchase_data(**params),
                retries=1,
            )
            if df is not None and not df.empty:
                return df, reason
        except Exception:
            continue
    return None, "所有回退组合均无数据"


# ============================================================
# 示例 1: 基本用法 - 获取单只股票回购数据
# ============================================================
def example_basic():
    """基本用法: 获取全市场回购数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取回购数据")
    print("=" * 60)

    service = get_service()

    try:
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
            return

        print(f"命中策略: {hit_reason}")
        print_df_brief(stable_df(df), rows=10)

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 对比多只股票回购数据
# ============================================================
def example_compare_stocks():
    """获取回购数据概览"""
    print("\n" + "=" * 60)
    print("示例 2: 回购数据概览")
    print("=" * 60)

    service = get_service()

    try:
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
        else:
            print(f"命中策略: {hit_reason}")
            print(f"共 {len(df)} 条记录")
            print(stable_df(df).head(3).to_string(index=False))
    except Exception as e:
        print(f"获取失败 - {e}")


# ============================================================
# 示例 3: 不同时间区间
# ============================================================
def example_date_ranges():
    """获取回购数据"""
    print("\n" + "=" * 60)
    print("示例 3: 获取回购数据")
    print("=" * 60)

    service = get_service()

    try:
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
        else:
            print(f"命中策略: {hit_reason}")
            print(f"共 {len(df)} 条回购记录")
    except Exception as e:
        print(f"获取失败 - {e}")


# ============================================================
# 示例 4: 统计分析
# ============================================================
def example_statistics():
    """对回购数据进行统计分析"""
    print("\n" + "=" * 60)
    print("示例 4: 回购数据统计分析")
    print("=" * 60)

    service = get_service()

    try:
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
            return

        print(f"命中策略: {hit_reason}")
        print(f"共 {len(df)} 条回购记录")
        print(f"字段列表: {list(df.columns)}")

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            print("\n数值字段统计:")
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_compare_stocks()
    example_date_ranges()
    example_statistics()
