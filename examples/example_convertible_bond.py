"""
可转债相关接口示例

演示如何使用 DataService 获取可转债数据。

包含三个接口:
1. get_conversion_bond_list() - 获取可转债列表
   - 无必需参数
   - 返回: DataFrame - 包含所有可转债的基本信息

2. get_conversion_bond_daily(symbol, start_date, end_date) - 获取可转债日线数据
   - symbol: 可转债代码 (如 "127045" 或 "sh127045")
   - start_date/end_date: 可选，格式 "YYYY-MM-DD"
   - 返回: DataFrame - 指定可转债的历史日线数据

3. calculate_conversion_value() - 计算转股价值
   - bond_price: 可转债价格
   - conversion_ratio: 转股比例
   - stock_price: 正股价格
   - 返回: dict - 包含转股价值和溢价率

注意: 接口通过 service.get_conversion_bond_list() 和 service.get_conversion_bond_daily() 访问。
若接口不可用，会使用演示数据。
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import akshare as ak
from _example_utils import (
    fetch_with_retry,
    normalize_symbol_input,
    print_df_brief,
    stable_df,
)


def calculate_conversion_value(
    bond_price: float,
    conversion_ratio: float,
    stock_price: float,
) -> dict:
    """本地计算转股价值与溢价率（避免依赖 adapter 私有方法）。"""
    conversion_value = conversion_ratio * stock_price
    premium_rate = ((bond_price - conversion_value) / conversion_value) * 100
    return {
        "bond_price": bond_price,
        "conversion_ratio": conversion_ratio,
        "stock_price": stock_price,
        "conversion_value": conversion_value,
        "premium_rate": premium_rate,
    }


def _mock_bond_list():
    """返回模拟的可转债列表数据用于演示"""
    return pd.DataFrame({
        "bond_code": ["127045", "110059", "123107", "113050", "128143", "113052", "127046"],
        "bond_name": ["牧原转债", "南航转债", "蓝盾转债", "南银转债", "锋龙转债", "兴业转债", "中装转债"],
        "stock_code": ["002714", "601111", "300297", "601009", "002931", "601166", "002822"],
        "stock_name": ["牧原股份", "中国国航", "蓝盾股份", "南京银行", "锋龙股份", "兴业银行", "中装建设"],
        "list_date": ["2021-09-06", "2021-09-13", "2020-12-15", "2021-03-24", "2021-03-30", "2022-01-18", "2021-05-07"],
        "maturity_date": ["2027-09-06", "2027-09-13", "2026-12-15", "2027-03-24", "2027-03-30", "2028-01-18", "2027-05-07"],
        "face_value": [100.0] * 7,
        "issue_size": [90.0, 100.0, 4.0, 200.0, 2.45, 500.0, 11.6],
        "credit_rating": ["AA+", "AAA", "A+", "AAA", "A+", "AAA", "AA"],
    })


def _mock_daily_data(symbol="127045"):
    """返回模拟的可转债日线数据用于演示"""
    dates = pd.date_range(start="2024-01-01", end="2024-03-31", freq="B")
    n = len(dates)
    base_price = 120.0
    prices = base_price + (pd.Series(range(n)) * 0.1) + (pd.Series(range(n)).apply(lambda x: (x % 5 - 2) * 0.5))
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": prices - 0.2,
        "high": prices + 0.5,
        "low": prices - 0.5,
        "close": prices,
        "volume": [50000 + (i % 10) * 5000 for i in range(n)],
        "amount": [6000000 + (i % 10) * 600000 for i in range(n)],
    })


# ============================================================
# 示例 1: 获取可转债列表
# ============================================================
def example_convert_bond_list():
    """获取可转债列表"""
    print("=" * 60)
    print("示例 1: 获取可转债列表")
    print("=" * 60)

    from akshare_data import get_service

    service = get_service()
    try:
        df = fetch_with_retry(lambda: service.get_conversion_bond_list(), retries=2)
    except Exception as e:
        print(f"获取数据失败: {e}")
        try:
            df = ak.bond_zh_cov()
            if df is not None and not df.empty:
                print("[AkShare fallback success]")
        except Exception:
            df = None

    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        print("[数据未下载，使用演示数据]")
        df = _mock_bond_list()

    print_df_brief(stable_df(df), rows=10)


# ============================================================
# 示例 2: 获取可转债日线数据
# ============================================================
def example_convert_bond_daily():
    """获取单只可转债的日线数据"""
    print("\n" + "=" * 60)
    print("示例 2: 获取可转债日线数据")
    print("=" * 60)

    from akshare_data import get_service

    service = get_service()
    try:
        df = fetch_with_retry(
            lambda: service.get_conversion_bond_daily(
                symbol=normalize_symbol_input("127045"),
                start_date="2024-01-01",
                end_date="2024-03-31",
            ),
            retries=2,
        )
    except Exception as e:
        print(f"获取数据失败: {e}")
        df = None

    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        print("[数据未下载，使用演示数据]")
        df = _mock_daily_data()

    print_df_brief(stable_df(df), rows=10)


# ============================================================
# 示例 3: 可转债日线数据 (带交易所前缀)
# ============================================================
def example_convert_bond_daily_with_prefix():
    """带交易所前缀的可转债代码"""
    print("\n" + "=" * 60)
    print("示例 3: 带交易所前缀的可转债代码")
    print("=" * 60)

    from akshare_data import get_service

    service = get_service()
    try:
        df = fetch_with_retry(
            lambda: service.get_conversion_bond_daily(
                symbol=normalize_symbol_input("sh110059"),
                start_date="2024-01-01",
                end_date="2024-01-31",
            ),
            retries=2,
        )
    except Exception as e:
        print(f"获取数据失败: {e}")
        df = None

    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        print("[数据未下载，使用演示数据]")
        df = _mock_daily_data("110059")

    print_df_brief(stable_df(df), rows=10)


# ============================================================
# 示例 4: 计算转股价值
# ============================================================
def example_conversion_value():
    """计算可转债的转股价值和溢价率"""
    print("\n" + "=" * 60)
    print("示例 4: 计算转股价值")
    print("=" * 60)

    result = calculate_conversion_value(
        bond_price=120.5,
        conversion_ratio=8.5,
        stock_price=14.2,
    )

    print("计算结果:")
    print(f"  可转债价格: {result['bond_price']:.2f} 元")
    print(f"  转股比例: {result['conversion_ratio']:.2f}")
    print(f"  正股价格: {result['stock_price']:.2f} 元")
    print(f"  转股价值: {result['conversion_value']:.2f} 元")
    print(f"  转股溢价率: {result['premium_rate']:.2f}%")

    if result["premium_rate"] < 0:
        print("\n  转股溢价率为负，存在套利机会!")
    else:
        print("\n  转股溢价率为正，暂无套利机会")


# ============================================================
# 示例 5: 可转债列表筛选分析
# ============================================================
def example_convert_bond_analysis():
    """对可转债列表进行简单筛选分析"""
    print("\n" + "=" * 60)
    print("示例 5: 可转债列表筛选分析")
    print("=" * 60)

    from akshare_data import get_service

    service = get_service()
    try:
        df = fetch_with_retry(lambda: service.get_conversion_bond_list(), retries=2)
    except Exception as e:
        print(f"获取数据失败: {e}")
        try:
            df = ak.bond_zh_cov()
        except Exception:
            df = None

    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        print("[数据未下载，使用演示数据]")
        df = _mock_bond_list()

    print(f"可转债总数: {len(df)}")
    print(f"字段列表: {list(df.columns)}")

    price_col = None
    for col in df.columns:
        if "价格" in str(col) or "price" in str(col).lower():
            price_col = col
            break

    if price_col:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
        low_price = df[df[price_col] < 100]
        print(f"\n价格低于100元的可转债: {len(low_price)} 只")
        if not low_price.empty:
            print(low_price.head(5).to_string(index=False))
    else:
        print("\n无价格列，显示前5行数据:")
        print(df.head(5).to_string(index=False))


# ============================================================
# 示例 6: 批量获取可转债日线数据
# ============================================================
def example_batch_convert_bond_daily():
    """批量获取多只可转债的日线数据"""
    print("\n" + "=" * 60)
    print("示例 6: 批量获取可转债日线数据")
    print("=" * 60)

    from akshare_data import get_service

    bond_codes = ["127045", "110059", "123107"]

    service = get_service()
    for code in bond_codes:
        try:
            norm_code = normalize_symbol_input(code)
            df = fetch_with_retry(
                lambda: service.get_conversion_bond_daily(
                    symbol=norm_code,
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                ),
                retries=2,
            )
        except Exception as e:
            print(f"\n可转债 {code}: 获取失败 - {e}")
            continue
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            print(f"\n可转债 {code}: [数据未下载]")
            continue
        print(f"\n可转债 {code}:")
        print(f"  数据行数: {len(df)}")
        if "close" in df.columns:
            print(f"  收盘价范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
        else:
            print("  无收盘价数据")


if __name__ == "__main__":
    example_convert_bond_list()
    example_convert_bond_daily()
    example_convert_bond_daily_with_prefix()
    example_conversion_value()
    example_convert_bond_analysis()
    example_batch_convert_bond_daily()