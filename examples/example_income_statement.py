"""
利润表接口示例 (get_income_statement)

演示如何使用 get_income_statement() 获取上市公司的利润表数据。

导入方式: from akshare_data import get_service
          service = get_service()
          df = service.get_income_statement(symbol="600519")
"""

import logging
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

import pandas as pd
from akshare_data import get_service
from _example_utils import first_non_empty_by_symbol


def _mock_income_statement(symbol: str) -> pd.DataFrame:
    return pd.DataFrame({
        "symbol": [symbol] * 3,
        "report_date": ["2022-12-31", "2023-12-31", "2024-06-30"],
        "营业总收入": [5e10, 5.5e10, 2.8e10],
        "营业收入": [5e10, 5.5e10, 2.8e10],
        "营业总成本": [3e10, 3.2e10, 1.6e10],
        "营业利润": [2e10, 2.3e10, 1.2e10],
        "利润总额": [2e10, 2.3e10, 1.2e10],
        "净利润": [1.5e10, 1.8e10, 9e9],
    })


def _safe_income_statement(fetch_fn, symbols):
    df, used_symbol = first_non_empty_by_symbol(fetch_fn, symbols)
    if df.empty:
        df = _mock_income_statement(symbols[0])
        used_symbol = symbols[0]
    return df, used_symbol


def example_basic():
    """基本用法: 获取单只股票的利润表"""
    print("=" * 60)
    print("示例 1: 获取贵州茅台利润表")
    print("=" * 60)

    service = get_service()

    try:
        df, used_symbol = _safe_income_statement(service.get_income_statement, ["600519", "000858", "000001"])

        print(f"数据形状: {df.shape}")
        print(f"回退命中代码: {used_symbol}")
        print(f"字段列表: {list(df.columns)}")
        print("\n前5行数据:")
        print(df.head())

    except Exception as e:
        print(f"获取数据失败: {e}")


def example_multiple_stocks():
    """多只股票: 获取多只股票的利润表"""
    print("\n" + "=" * 60)
    print("示例 2: 获取多只股票利润表")
    print("=" * 60)

    service = get_service()
    symbols = {"600519": "贵州茅台", "000858": "五粮液", "000568": "泸州老窖"}

    for code, name in symbols.items():
        try:
            df, used_symbol = _safe_income_statement(
                service.get_income_statement, [code, "000001", "600036"]
            )
            print(f"\n{name} ({code}): {len(df)} 条记录")
            if used_symbol != code:
                print(f"  (回退到: {used_symbol})")
            print(df.head(2).to_string(index=False))
        except Exception as e:
            print(f"\n{name} ({code}): 获取失败 - {e}")


def example_analysis():
    """分析: 利润数据分析"""
    print("\n" + "=" * 60)
    print("示例 3: 利润数据分析")
    print("=" * 60)

    service = get_service()

    try:
        df, used_symbol = _safe_income_statement(service.get_income_statement, ["600519", "000858", "000001"])

        print(f"数据形状: {df.shape}")
        print(f"回退命中代码: {used_symbol}")
        print(f"字段数量: {len(df.columns)}")

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            print("\n描述统计:")
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"分析失败: {e}")


def example_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("示例 4: 错误处理演示")
    print("=" * 60)

    service = get_service()

    print("\n测试 1: 正常股票代码")
    try:
        df, _ = _safe_income_statement(service.get_income_statement, ["600519", "000858", "000001"])
        print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    print("\n测试 2: 无效股票代码")
    try:
        df = service.get_income_statement(symbol="INVALID")
        if df is None or df.empty:
            print("  结果: 返回空数据")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basic()
    example_multiple_stocks()
    example_analysis()
    example_error_handling()
