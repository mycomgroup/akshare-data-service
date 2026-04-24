"""get_repurchase_data() 接口示例

演示如何使用 akshare_data.get_repurchase_data() 获取股票回购数据。

返回字段: 包含股票代码、回购价格、回购数量、回购金额等。
"""

<<<<<<< HEAD
from __future__ import annotations

import logging
import sys
import time
import warnings
from typing import Callable, Optional

import pandas as pd

sys.warnoptions = ["ignore::DeprecationWarning"]
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from akshare_data import get_service


def _fetch_with_retry(fetcher: Callable[[], pd.DataFrame], desc: str, retries: int = 3) -> Optional[pd.DataFrame]:
    last_error: Optional[Exception] = None
    for i in range(retries):
        try:
            df = fetcher()
            if df is not None and not df.empty:
                return df
            print(f"{desc}: 第 {i + 1}/{retries} 次返回空结果")
        except Exception as e:
            last_error = e
            print(f"{desc}: 第 {i + 1}/{retries} 次失败 -> {e}")
        if i < retries - 1:
            time.sleep(1)
    if last_error is not None:
        print(f"{desc}: 重试后仍失败，最终异常: {last_error}")
    return None


def _get_repurchase_df(service) -> Optional[pd.DataFrame]:
    df = _fetch_with_retry(lambda: service.get_repurchase_data(), "service.get_repurchase_data")
    if df is not None:
        return df
    return _fetch_with_retry(lambda: service.akshare.get_repurchase_data(), "service.akshare.get_repurchase_data")


def _print_df(df: pd.DataFrame, title: str, rows: int = 10) -> None:
    if df is None:
        print(f"{title}: None")
        return
    print(f"{title}: shape={df.shape}, columns={list(df.columns)}")
    if df.empty:
        print("  空数据")
        return
    print(df.head(rows).to_string(index=False))
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d


# ============================================================
# 示例 1: 基本用法 - 获取回购数据
# ============================================================
def example_basic() -> None:
    """基本用法: 获取全市场回购数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取回购数据")
    print("=" * 60)

    service = get_service()
    df = _get_repurchase_df(service)
    if df is None:
        print("最终无可用数据，可能是数据源暂时不可用。")
        return

<<<<<<< HEAD
    _print_df(df, "回购数据", rows=10)
=======
    try:
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
            return

        print(f"命中策略: {hit_reason}")
        print_df_brief(stable_df(df), rows=10)

    except Exception as e:
        print(f"获取数据失败: {e}")
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d


# ============================================================
# 示例 2: 回购数据概览
# ============================================================
def example_overview() -> None:
    """获取回购数据概览"""
    print("\n" + "=" * 60)
    print("示例 2: 回购数据概览")
    print("=" * 60)

    service = get_service()
    df = _get_repurchase_df(service)
    if df is None:
        print("最终无可用数据")
        return

<<<<<<< HEAD
    print(f"共 {len(df)} 条记录")
    _print_df(df, "数据预览", rows=3)
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d


# ============================================================
# 示例 3: 回购数据分析
# ============================================================
def example_analysis() -> None:
    """对回购数据进行简单分析"""
    print("\n" + "=" * 60)
    print("示例 3: 回购数据分析")
    print("=" * 60)

    service = get_service()
    df = _get_repurchase_df(service)
    if df is None:
        print("最终无可用数据")
        return

    print(f"共 {len(df)} 条回购记录")
    print(f"字段列表: {list(df.columns)}")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        print("\n数值字段统计:")
        print(df[numeric_cols].describe().to_string())


# ============================================================
# 示例 4: 不同数据源对比
# ============================================================
def example_source_comparison() -> None:
    """对比 DataService 和 AkShare adapter 的调用方式"""
    print("\n" + "=" * 60)
    print("示例 4: DataService vs AkShare 调用方式对比")
    print("=" * 60)

    service = get_service()

    print("\n方式1: DataService.get_repurchase_data()")
    try:
<<<<<<< HEAD
        df1 = _fetch_with_retry(lambda: service.get_repurchase_data(), "DataService", retries=1)
        if df1 is not None and not df1.empty:
            print(f"  结果: {df1.shape}")
        else:
            print("  结果: 无数据（缓存可能为空，需要先下载数据）")
=======
        df, hit_reason = _fetch_repurchase_with_fallback(service)
        if df is None or df.empty:
            print("无数据")
        else:
            print(f"命中策略: {hit_reason}")
            print(f"共 {len(df)} 条回购记录")
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
    except Exception as e:
        print(f"  失败: {e}")

    print("\n方式2: service.akshare.get_repurchase_data()")
    try:
<<<<<<< HEAD
        df2 = _fetch_with_retry(lambda: service.akshare.get_repurchase_data(), "AkShare")
        if df2 is not None:
            print(f"  结果: {df2.shape}")
            _print_df(df2, "AkShare 直调结果", rows=5)
        else:
            print("  结果: 无数据")
=======
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

>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
    except Exception as e:
        print(f"  失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_overview()
    example_analysis()
    example_source_comparison()