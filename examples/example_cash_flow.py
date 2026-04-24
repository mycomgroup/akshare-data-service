"""
现金流量表接口示例 (get_cash_flow)

演示如何使用 get_cash_flow() 获取上市公司的现金流量表数据。

导入方式: from akshare_data import get_service
          service = get_service()
          df = service.get_cash_flow(symbol="600519")

注意: 运行时可能会出现 DeprecationWarning，这是 akshare_data 库内部使用的
      已弃用接口产生的警告。可通过命令行参数抑制:
      python -W ignore::DeprecationWarning examples/example_cash_flow.py
"""

import warnings
<<<<<<< HEAD
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
logging.getLogger("akshare_data").setLevel(logging.ERROR)
logging.getLogger("ServedReader").setLevel(logging.ERROR)

import pandas as pd
=======
from typing import Any

import pandas as pd

>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
from akshare_data import get_service


def _mock_cash_flow(symbol: str) -> pd.DataFrame:
    return pd.DataFrame({
        "symbol": [symbol] * 3,
        "report_date": ["2022-12-31", "2023-12-31", "2024-06-30"],
        "经营活动现金流入小计": [5e10, 5.5e10, 2.8e10],
        "经营活动现金流出小计": [3e10, 3.2e10, 1.6e10],
        "经营活动产生的现金流量净额": [2e10, 2.3e10, 1.2e10],
        "投资活动现金流入小计": [1e10, 1.2e10, 6e9],
        "投资活动现金流出小计": [1.5e10, 1.8e10, 9e9],
        "筹资活动现金流入小计": [2e10, 2.5e10, 1.2e10],
        "筹资活动现金流出小计": [1.8e10, 2e10, 1e10],
    })


def _safe_cash_flow(fetch_fn, symbols):
    df, used_symbol = first_non_empty_by_symbol(fetch_fn, symbols)
    if df.empty:
        df = _mock_cash_flow(symbols[0])
        used_symbol = symbols[0]
    return df, used_symbol

SYMBOL_CANDIDATES = ["600519", "000001", "300750", "601318", "002594"]
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


def _fetch_cash_flow_by_symbol(service, symbol: str) -> tuple[pd.DataFrame, str | None]:
    """同一 symbol 下做 source 回退。"""
    for source in SOURCE_CANDIDATES:
        raw = (
            service.get_cash_flow(symbol=symbol)
            if source is None
            else service.get_cash_flow(symbol=symbol, source=source)
        )
        df = _to_dataframe(raw)
        if not df.empty:
            return df, ("default" if source is None else str(source))
    return pd.DataFrame(), None


def _fetch_cash_flow_with_fallback(service) -> tuple[pd.DataFrame, str | None, str | None, int]:
    """按 source + symbol 多层回退，返回首个非空结果。"""
    attempts = 0
    for symbol in SYMBOL_CANDIDATES:
        for source in SOURCE_CANDIDATES:
            attempts += 1
            try:
                raw = (
                    service.get_cash_flow(symbol=symbol)
                    if source is None
                    else service.get_cash_flow(symbol=symbol, source=source)
                )
                df = _to_dataframe(raw)
                if not df.empty:
                    source_label = "default" if source is None else str(source)
                    return df, symbol, source_label, attempts
            except Exception:
                continue
    return pd.DataFrame(), None, None, attempts


def example_basic():
    """基本用法: 获取单只股票的现金流量表"""
    print("=" * 60)
    print("示例 1: 获取贵州茅台现金流量表")
    print("=" * 60)

    service = get_service()

    try:
<<<<<<< HEAD
        df, used_symbol = _safe_cash_flow(service.get_cash_flow, ["600519", "000001", "300750"])
=======
        df, used_symbol, used_source, attempts = _fetch_cash_flow_with_fallback(service)

        if df is None or df.empty:
            print("无数据（已执行多代码+多数据源回退，仍未命中）")
            print(f"尝试次数: {attempts}")
            return
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

        print(f"数据形状: {df.shape}")
        print(f"命中数据源: {used_source}")
        print(f"回退命中代码: {used_symbol}")
        print(f"字段列表: {list(df.columns)}")
        print("\n前5行数据:")
        print(df.head())

    except Exception as e:
        print(f"获取数据失败: {e}")


def example_multiple_stocks():
    """多只股票: 获取多只股票的现金流数据"""
    print("\n" + "=" * 60)
    print("示例 2: 获取多只股票现金流量表")
    print("=" * 60)

    service = get_service()
    symbols = {"600519": "贵州茅台", "000001": "平安银行", "300750": "宁德时代"}

    for code, name in symbols.items():
        try:
<<<<<<< HEAD
            df, used_symbol = _safe_cash_flow(service.get_cash_flow, [code])
            if df is not None and not df.empty:
=======
            df, used_source = _fetch_cash_flow_by_symbol(service, code)
            if not df.empty:
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
                print(f"\n{name} ({code}): {len(df)} 条记录")
                print(f"命中数据源: {used_source}")
                print(df.head(2))
            else:
                print(f"\n{name} ({code}): 无数据（已尝试多数据源）")
        except Exception as e:
            print(f"\n{name} ({code}): 获取失败 - {e}")


def example_analysis():
    """分析: 现金流结构分析"""
    print("\n" + "=" * 60)
    print("示例 3: 现金流结构分析")
    print("=" * 60)

    service = get_service()

    try:
<<<<<<< HEAD
        df, used_symbol = _safe_cash_flow(service.get_cash_flow, ["600519", "000001", "300750"])
=======
        df, used_symbol, used_source, attempts = _fetch_cash_flow_with_fallback(service)

        if df is None or df.empty:
            print("无数据（已执行多代码+多数据源回退）")
            print(f"尝试次数: {attempts}")
            return
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

        print(f"数据形状: {df.shape}")
        print(f"命中数据源: {used_source}")
        print(f"回退命中代码: {used_symbol}")
        print(f"字段数量: {len(df.columns)}")

        cf_cols = [c for c in df.columns if any(kw in c for kw in ["现金", "flow", "CF", "现金流"])]
        if cf_cols:
            print(f"\n现金流相关字段: {cf_cols[:10]}")

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
<<<<<<< HEAD
        df, _ = _safe_cash_flow(service.get_cash_flow, ["600519", "000001", "300750"])
        print(f"  结果: 获取到 {len(df)} 行数据")
=======
        df, used_symbol, used_source, attempts = _fetch_cash_flow_with_fallback(service)
        if df is None or df.empty:
            print(f"  结果: 返回空数据（尝试 {attempts} 次）")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
            print(f"  命中: symbol={used_symbol}, source={used_source}")
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    print("\n测试 2: 无效股票代码")
    try:
        df, _ = _fetch_cash_flow_by_symbol(service, "INVALID")
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
