"""
涨跌停池接口使用示例

本示例展示如何通过 DataService 的 akshare adapter 获取涨跌停池数据。
包含两个接口：
  - get_limit_up_pool(date): 获取指定日期的涨停池数据
  - get_limit_down_pool(date): 获取指定日期的跌停池数据

参数说明：
    date: 必填，查询日期，格式 "YYYY-MM-DD"（内部会自动转换为 YYYYMMDD）

返回：
    pd.DataFrame，包含涨跌停股票的详细信息，如：
        - 代码/名称
        - 涨跌幅
        - 最新价
        - 涨停/跌停价
        - 连板天数
        - 所属行业等
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import time
from typing import Callable, Optional

import pandas as pd
import akshare as ak



def _fetch_with_retry(fetcher: Callable[[], pd.DataFrame], desc: str) -> Optional[pd.DataFrame]:
    for i in range(3):
        try:
            df = fetcher()
            if df is not None and not df.empty:
                return df
            print(f"{desc}: 第 {i + 1}/3 次返回空结果")
        except Exception as e:  # noqa: BLE001
            print(f"{desc}: 第 {i + 1}/3 次失败 -> {e}")
        time.sleep(1)
    return None


def example_basic_limit_up():
    """基础用法：获取指定日期的涨停池数据"""
    print("=" * 60)
    print("示例1: 获取指定日期的涨停池数据")
    print("=" * 60)

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_up_pool_em(date="20260417"),
            "limit_up_pool_em(20260417)",
        )

        if df is not None:
            print(f"数据形状: {df.shape}")
            print(f"涨停股票数量: {len(df)}")
            print(f"列名: {df.columns.tolist()}")
            print("\n前5行数据:")
            print(df.head())
        else:
            print("该日期无涨停数据（重试后仍为空）")
    except Exception as e:
        print(f"获取涨停池数据失败: {e}")


def example_basic_limit_down():
    """基础用法：获取指定日期的跌停池数据"""
    print("\n" + "=" * 60)
    print("示例2: 获取指定日期的跌停池数据")
    print("=" * 60)

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_down_pool_em(date="20260417"),
            "limit_down_pool_em(20260417)",
        )

        if df is not None:
            print(f"数据形状: {df.shape}")
            print(f"跌停股票数量: {len(df)}")
            print(f"列名: {df.columns.tolist()}")
            print("\n前5行数据:")
            print(df.head())
        else:
            print("该日期无跌停数据（重试后仍为空）")
    except Exception as e:
        print(f"获取跌停池数据失败: {e}")


def example_compare_limit_up_down():
    """对比同一天的涨停和跌停数量"""
    print("\n" + "=" * 60)
    print("示例3: 对比同一天的涨停和跌停数量")
    print("=" * 60)

    dates = [
        "20260413",
        "20260414",
        "20260415",
        "20260416",
        "20260417",
    ]

    print(f"{'日期':<12} {'涨停数量':>8} {'跌停数量':>8}")
    print("-" * 30)

    for date in dates:
        try:
            up_df = _fetch_with_retry(
                lambda d=date: ak.limit_up_pool_em(date=d),
                f"limit_up_pool_em({date})",
            )
            down_df = _fetch_with_retry(
                lambda d=date: ak.limit_down_pool_em(date=d),
                f"limit_down_pool_em({date})",
            )
            print(f"{date:<12} {len(up_df) if up_df is not None else 0:>8} {len(down_df) if down_df is not None else 0:>8}")
        except Exception:
            print(f"{date:<12} {'获取失败':>8}")


def example_limit_up_analysis():
    """涨停池数据分析：统计连板情况"""
    print("\n" + "=" * 60)
    print("示例4: 涨停池数据分析 - 连板统计")
    print("=" * 60)

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_up_pool_em(date="20260417"),
            "limit_up_pool_em(analysis)",
        )

        if df is None:
            print("该日期无涨停数据")
        else:
            print(f"共 {len(df)} 只股票涨停")

            print("\n数据列:")
            for i, col in enumerate(df.columns):
                print(f"  {i + 1}. {col}")

            print("\n前10行详细数据:")
            print(df.head(10))

            possible_cols = ["连板数", "连板天数", "continuous_limit_up", "连板"]
            board_col = None
            for col in possible_cols:
                if col in df.columns:
                    board_col = col
                    break

            if board_col:
                print(f"\n连板统计（基于'{board_col}'列）:")
                print(df[board_col].value_counts().sort_index())
            else:
                print("\n未找到连板天数字段")
    except Exception as e:
        print(f"获取涨停池数据失败: {e}")


def example_limit_down_analysis():
    """跌停池数据分析"""
    print("\n" + "=" * 60)
    print("示例5: 跌停池数据分析")
    print("=" * 60)

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_down_pool_em(date="20260417"),
            "limit_down_pool_em(analysis)",
        )

        if df is None:
            print("该日期无跌停数据（市场情绪较好）")
        else:
            print(f"共 {len(df)} 只股票跌停")
            print("\n数据列:")
            for col in df.columns:
                print(f"  - {col}")
            print("\n详细数据:")
            print(df)
    except Exception as e:
        print(f"获取跌停池数据失败: {e}")


def example_limit_up_down_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("示例6: 错误处理示例")
    print("=" * 60)

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_up_pool_em(date="20260210"),
            "limit_up_pool_em(non_trading)",
        )
        if df is None:
            print("非交易日涨停池返回空DataFrame")
        else:
            print(f"获取到 {len(df)} 条涨停数据")
    except Exception as e:
        print(f"捕获到异常: {type(e).__name__}: {e}")

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_down_pool_em(date="20260210"),
            "limit_down_pool_em(non_trading)",
        )
        if df is None:
            print("非交易日跌停池返回空DataFrame")
        else:
            print(f"获取到 {len(df)} 条跌停数据")
    except Exception as e:
        print(f"捕获到异常: {type(e).__name__}: {e}")

    try:
        df = _fetch_with_retry(
            lambda: ak.limit_up_pool_em(date="invalid"),
            "limit_up_pool_em(invalid)",
        )
        print(f"获取到 {len(df) if df is not None else 0} 条数据")
    except Exception as e:
        print(f"捕获到异常: {type(e).__name__}: {e}")


def example_market_sentiment():
    """实用场景：市场情绪分析"""
    print("\n" + "=" * 60)
    print("示例7: 市场情绪分析 - 涨跌停比")
    print("=" * 60)

    dates = [
        "20260413",
        "20260414",
        "20260415",
        "20260416",
        "20260417",
    ]

    print(f"{'日期':<12} {'涨停':>6} {'跌停':>6} {'涨跌停比':>8} {'情绪判断':>8}")
    print("-" * 45)

    for date in dates:
        try:
            up_df = _fetch_with_retry(
                lambda d=date: ak.limit_up_pool_em(date=d),
                f"limit_up_pool_em({date})",
            )
            down_df = _fetch_with_retry(
                lambda d=date: ak.limit_down_pool_em(date=d),
                f"limit_down_pool_em({date})",
            )

            up_count = len(up_df) if up_df is not None else 0
            down_count = len(down_df) if down_df is not None else 0

            if down_count > 0:
                ratio = up_count / down_count
            else:
                ratio = float("inf")

            if ratio >= 5:
                sentiment = "极好"
            elif ratio >= 2:
                sentiment = "偏强"
            elif ratio >= 1:
                sentiment = "中性"
            else:
                sentiment = "偏弱"

            ratio_str = f"{ratio:.1f}" if ratio != float("inf") else "∞"
            print(
                f"{date:<12} {up_count:>6} {down_count:>6} {ratio_str:>8} {sentiment:>8}"
            )
        except Exception:
            print(f"{date:<12} {'获取失败':>6}")


if __name__ == "__main__":
    example_basic_limit_up()
    example_basic_limit_down()
    example_compare_limit_up_down()
    example_limit_up_analysis()
    example_limit_down_analysis()
    example_limit_up_down_error_handling()
    example_market_sentiment()