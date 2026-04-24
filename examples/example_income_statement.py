"""
利润表接口示例 (get_income_statement)

演示如何使用 get_income_statement() 获取上市公司的利润表数据。

导入方式: from akshare_data import get_service
          service = get_service()
          df = service.get_income_statement(symbol="600519")
"""

import logging
import warnings
from typing import Any

import pandas as pd

from akshare_data import get_service

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

SYMBOL_CANDIDATES = ["600519", "000858", "000001", "000568", "601318"]
SOURCE_CANDIDATES: list[str | list[str] | None] = [
    None,
    "lixinger",
    "akshare",
    ["lixinger", "akshare"],
    ["akshare", "lixinger"],
]


def _to_dataframe(value: Any) -> pd.DataFrame:
    """兼容不同数据源返回结构，统一转换为 DataFrame。"""
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, dict):
        for key in ("data", "result", "items", "rows"):
            data = value.get(key)
            if isinstance(data, pd.DataFrame):
                return data
            if isinstance(data, (list, tuple)):
                return pd.DataFrame(data)
        return pd.DataFrame([value]) if value else pd.DataFrame()
    if isinstance(value, (list, tuple)):
        return pd.DataFrame(value)
    return pd.DataFrame()


def _fetch_income_by_symbol(service, symbol: str) -> tuple[pd.DataFrame, str | None]:
    """同一 symbol 下做 source 回退。"""
    for source in SOURCE_CANDIDATES:
        raw = (
            service.get_income_statement(symbol=symbol)
            if source is None
            else service.get_income_statement(symbol=symbol, source=source)
        )
        df = _to_dataframe(raw)
        if not df.empty:
            return df, ("default" if source is None else str(source))
    return pd.DataFrame(), None


def _fetch_income_with_fallback(service) -> tuple[pd.DataFrame, str | None, str | None, int]:
    """按 source + symbol 多层回退，返回首个非空结果。"""
    attempts = 0
    for symbol in SYMBOL_CANDIDATES:
        for source in SOURCE_CANDIDATES:
            attempts += 1
            try:
                raw = (
                    service.get_income_statement(symbol=symbol)
                    if source is None
                    else service.get_income_statement(symbol=symbol, source=source)
                )
                df = _to_dataframe(raw)
                if not df.empty:
                    source_label = "default" if source is None else str(source)
                    return df, symbol, source_label, attempts
            except Exception:
                continue
    return pd.DataFrame(), None, None, attempts


def example_basic():
    """基本用法: 获取单只股票的利润表"""
    print("=" * 60)
    print("示例 1: 获取贵州茅台利润表")
    print("=" * 60)

    service = get_service()

    try:
        df, used_symbol, used_source, attempts = _fetch_income_with_fallback(service)

        if df is None or df.empty:
            print("无数据（已执行多代码+多数据源回退，仍未命中）")
            print(f"尝试次数: {attempts}")
            return

        print(f"数据形状: {df.shape}")
        print(f"命中数据源: {used_source}")
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
            df, used_source = _fetch_income_by_symbol(service, code)
            if not df.empty:
                print(f"\n{name} ({code}): {len(df)} 条记录")
                print(f"命中数据源: {used_source}")
                print(df.head(2))
            else:
                print(f"\n{name} ({code}): 无数据（已尝试多数据源）")
        except Exception as e:
            print(f"\n{name} ({code}): 获取失败 - {e}")


def example_analysis():
    """分析: 利润数据分析"""
    print("\n" + "=" * 60)
    print("示例 3: 利润数据分析")
    print("=" * 60)

    service = get_service()

    try:
        df, used_symbol, used_source, attempts = _fetch_income_with_fallback(service)

        if df is None or df.empty:
            print("无数据（已执行多代码+多数据源回退）")
            print(f"尝试次数: {attempts}")
            return

        print(f"数据形状: {df.shape}")
        print(f"命中数据源: {used_source}")
        print(f"回退命中代码: {used_symbol}")
        print(f"字段数量: {len(df.columns)}")

        # 数值列统计
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
        df, used_symbol, used_source, attempts = _fetch_income_with_fallback(service)
        if df is None or df.empty:
            print(f"  结果: 返回空数据（尝试 {attempts} 次）")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
            print(f"  命中: symbol={used_symbol}, source={used_source}")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    print("\n测试 2: 无效股票代码")
    try:
        df, _ = _fetch_income_by_symbol(service, "INVALID")
        if df is None or df.empty:
            print("  结果: 返回空数据（符合预期）")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basic()
    example_multiple_stocks()
    example_analysis()
    example_error_handling()
