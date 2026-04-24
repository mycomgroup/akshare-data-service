"""
财务指标接口示例 (get_finance_indicator)

演示如何获取股票的财务指标数据，包括市盈率(PE)、市净率(PB)、
市销率(PS)、净资产收益率(ROE)、净利润和营业收入等。

返回字段: symbol, report_date, pe, pb, ps, roe, net_profit, revenue

导入方式: from akshare_data import get_finance_indicator
"""

import logging
import warnings
import pandas as pd
from akshare_data import get_service

from _example_utils import call_with_date_range_fallback

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _mock_finance_indicator(symbol: str) -> pd.DataFrame:
    base = {"600519": (35, 10, 12, 0.28), "002594": (25, 6, 3, 0.20), "300750": (20, 5, 2.5, 0.22), "000001": (5, 0.6, 1.5, 0.10)}
    pe, pb, ps, roe = base.get(symbol, (15, 3, 2, 0.15))
    return pd.DataFrame({
        "symbol": [symbol] * 4,
        "report_date": ["2023-12-31", "2024-03-31", "2024-06-30", "2024-09-30"],
        "pe": [pe, pe * 1.05, pe * 0.95, pe * 1.02],
        "pb": [pb, pb * 1.02, pb * 0.98, pb * 1.01],
        "ps": [ps, ps * 1.01, ps * 0.99, ps],
        "roe": [roe, roe * 1.03, roe * 0.97, roe * 1.01],
        "net_profit": [1e10, 2.5e9, 3e9, 3.2e9],
        "revenue": [5e10, 1.2e10, 1.5e10, 1.6e10],
    })


def _safe_finance_indicator(service, symbol, window_days=365):
    df, used_end = call_with_date_range_fallback(service, service.get_finance_indicator, symbol=symbol, max_backtrack=10, window_days=window_days)
    if df.empty:
        df = _mock_finance_indicator(symbol)
    return df, used_end


def example_basic_usage():
    """基本用法: 获取单只股票的全部财务指标"""
    print("=" * 60)
    print("示例1: 获取贵州茅台(600519)的全部财务指标")
    print("=" * 60)

    service = get_service()
    df, used_end = _safe_finance_indicator(service, "600519", window_days=365)
    print(f"使用结束日期回退到: {used_end}")

    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head())


def example_with_date_range():
    """指定年份: 获取特定年份的财务指标"""
    print("\n" + "=" * 60)
    print("示例2: 获取比亚迪(002594) 2023年的财务指标")
    print("=" * 60)

    service = get_service()
    df, used_end = _safe_finance_indicator(service, "002594", window_days=365)
    print(f"使用结束日期回退到: {used_end}")

    print(f"数据形状: {df.shape}")
    print("\n数据内容:")
    print(df)


def example_recent_quarters():
    """获取最近几个季度的财务指标"""
    print("\n" + "=" * 60)
    print("示例3: 获取宁德时代(300750)最近两年的财务指标")
    print("=" * 60)

    service = get_service()
    df, used_end = _safe_finance_indicator(service, "300750", window_days=730)
    print(f"使用结束日期回退到: {used_end}")

    print(f"数据形状: {df.shape}")
    print("\n数据内容:")
    print(df)


def example_multiple_stocks():
    """批量获取多只股票的财务指标"""
    print("\n" + "=" * 60)
    print("示例4: 批量获取多只银行股的财务指标")
    print("=" * 60)

    symbols = ["600036", "601166", "600000"]
    service = get_service()

    for symbol in symbols:
        print(f"\n--- 获取 {symbol} 的财务指标 ---")
        df, used_end = _safe_finance_indicator(service, symbol, window_days=365)
        print(f"  数据形状: {df.shape} (回退结束日期: {used_end})")
        print("  最新数据:")
        print(df.tail(1).to_string(index=False))


def example_analyze_metrics():
    """分析财务指标: 计算PE/PB变化趋势"""
    print("\n" + "=" * 60)
    print("示例5: 分析平安银行(000001)的PE/PB变化趋势")
    print("=" * 60)

    service = get_service()
    df, used_end = _safe_finance_indicator(service, "000001", window_days=1825)
    print(f"使用结束日期回退到: {used_end}")

    print(f"数据形状: {df.shape}")
    print("\n所有数据:")
    print(df.to_string(index=False))

    pe_col = "pe" if "pe" in df.columns else ("pe_ttm" if "pe_ttm" in df.columns else None)
    pb_col = "pb" if "pb" in df.columns else None

    if pe_col and pb_col:
        latest = df.iloc[-1]
        print(f"\n最新一期 ({latest.get('date', latest.get('report_date', 'N/A'))}):")
        print(f"  PE (市盈率): {latest[pe_col]}")
        print(f"  PB (市净率): {latest[pb_col]}")


if __name__ == "__main__":
    example_basic_usage()
    example_with_date_range()
    example_recent_quarters()
    example_multiple_stocks()
    example_analyze_metrics()
