"""
get_earnings_forecast() 接口示例

演示如何使用 akshare_data.get_earnings_forecast() 获取盈利预测数据。
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import akshare as ak
from akshare_data import get_service
from _example_utils import first_non_empty_by_symbol


def _get_earnings_forecast_with_fallback(symbol: str) -> tuple:
    service = get_service()
    df = service.get_earnings_forecast(symbol=symbol)
    if df is not None and not df.empty:
        return df, "service"
    try:
        df = ak.stock_profit_forecast(symbol=symbol)
        if df is not None and not df.empty:
            return df, "akshare"
    except Exception:
        pass
    return pd.DataFrame(), None


def example_basic():
    print("=" * 60)
    print("示例 1: 基本用法 - 获取盈利预测（股票代码回退）")
    print("=" * 60)
    try:
        df, used_symbol = first_non_empty_by_symbol(
            _get_earnings_forecast_with_fallback, ["600519", "000001", "300750"]
        )
        if df.empty:
            print("无数据")
            return
        print(f"回退命中代码: {used_symbol}")
        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")
        print(df.head())
    except Exception as e:
        print(f"获取数据失败: {e}")


def example_multi_stocks():
    print("\n" + "=" * 60)
    print("示例 2: 多只股票盈利预测")
    print("=" * 60)
    for symbol, name in [("600519", "贵州茅台"), ("000001", "平安银行"), ("300750", "宁德时代")]:
        try:
            df, source = _get_earnings_forecast_with_fallback(symbol)
            if df is None or df.empty:
                print(f"{name} ({symbol}): 无数据")
            else:
                print(f"{name} ({symbol}): {len(df)} 条 (来源: {source})")
                print(df.head(2).to_string(index=False))
        except Exception as e:
            print(f"{name} ({symbol}): 获取失败 - {e}")


def example_trend():
    print("\n" + "=" * 60)
    print("示例 3: 盈利预测统计")
    print("=" * 60)
    try:
        df, used_symbol = first_non_empty_by_symbol(
            _get_earnings_forecast_with_fallback, ["000001", "600519", "300750"]
        )
        if df.empty:
            print("无数据")
            return
        print(f"回退命中代码: {used_symbol}, 共 {len(df)} 条")
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            print(df[numeric_cols].describe())
    except Exception as e:
        print(f"获取数据失败: {e}")


def example_error_handling():
    print("\n" + "=" * 60)
    print("示例 4: 错误处理")
    print("=" * 60)
    service = get_service()
    try:
        df = service.get_earnings_forecast(symbol="INVALID")
        print(f"无效代码返回: {0 if df is None else len(df)} 行")
    except Exception as e:
        print(f"捕获异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basic()
    example_multi_stocks()
    example_trend()
    example_error_handling()
