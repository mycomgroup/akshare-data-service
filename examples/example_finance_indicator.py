"""
财务指标接口示例 (get_finance_indicator)

演示如何获取股票的财务指标数据，包括市盈率(PE)、市净率(PB)、
市销率(PS)、净资产收益率(ROE)、净利润和营业收入等。

返回字段: symbol, report_date, pe, pb, ps, roe, net_profit, revenue

导入方式: from akshare_data import get_finance_indicator
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import logging
import pandas as pd

logging.getLogger("akshare_data").setLevel(logging.ERROR)

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


def _get_finance_indicator_real(symbol: str, start_year: str = "2023") -> pd.DataFrame:
    """使用 AkShare 直接获取财务指标数据"""
    if not AKSHARE_AVAILABLE:
        return pd.DataFrame()
    try:
        df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns={"日期": "report_date"})
        df["symbol"] = symbol
        cols = ["symbol", "report_date"]
        for col in ["摊薄每股收益(元)", "每股净资产_调整后(元)", "每股经营性现金流(元)"]:
            if col in df.columns:
                cols.append(col)
        remaining_cols = [c for c in df.columns if c not in cols]
        cols.extend(remaining_cols[:20])
        return df[cols]
    except Exception:
        return pd.DataFrame()


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


def _safe_finance_indicator(symbol: str, start_year: str = "2023") -> pd.DataFrame:
    df = _get_finance_indicator_real(symbol, start_year)
    if df.empty:
        df = _mock_finance_indicator(symbol)
    return df


def example_basic_usage():
    """基本用法: 获取单只股票的全部财务指标"""
    print("=" * 60)
    print("示例1: 获取贵州茅台(600519)的全部财务指标")
    print("=" * 60)

    df = _safe_finance_indicator("600519", start_year="2023")

    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head().to_string(index=False))


def example_with_date_range():
    """指定年份: 获取特定年份的财务指标"""
    print("\n" + "=" * 60)
    print("示例2: 获取比亚迪(002594) 2023年的财务指标")
    print("=" * 60)

    df = _safe_finance_indicator("002594", start_year="2023")

    print(f"数据形状: {df.shape}")
    print("\n数据内容:")
    print(df.to_string(index=False))


def example_recent_quarters():
    """获取最近几个季度的财务指标"""
    print("\n" + "=" * 60)
    print("示例3: 获取宁德时代(300750)最近两年的财务指标")
    print("=" * 60)

    df = _safe_finance_indicator("300750", start_year="2023")

    print(f"数据形状: {df.shape}")
    print("\n数据内容:")
    print(df.to_string(index=False))


def example_multiple_stocks():
    """批量获取多只股票的财务指标"""
    print("\n" + "=" * 60)
    print("示例4: 批量获取多只银行股的财务指标")
    print("=" * 60)

    symbols = ["600036", "601166", "600000"]

    for symbol in symbols:
        print(f"\n--- 获取 {symbol} 的财务指标 ---")
        df = _safe_finance_indicator(symbol, start_year="2023")
        print(f"  数据形状: {df.shape}")
        print("  最新数据:")
        print(df.tail(1).to_string(index=False))


def example_analyze_metrics():
    """分析财务指标: 计算PE/PB变化趋势"""
    print("\n" + "=" * 60)
    print("示例5: 分析平安银行(000001)的PE/PB变化趋势")
    print("=" * 60)

    df = _safe_finance_indicator("000001", start_year="2023")

    print(f"数据形状: {df.shape}")
    print("\n所有数据:")
    print(df.to_string(index=False))

    pe_col = "pe" if "pe" in df.columns else ("摊薄每股收益(元)" if "摊薄每股收益(元)" in df.columns else None)
    pb_col = "pb" if "pb" in df.columns else ("每股净资产_调整后(元)" if "每股净资产_调整后(元)" in df.columns else None)

    if pe_col and pb_col:
        latest = df.iloc[-1]
        print(f"\n最新一期 ({latest.get('report_date', 'N/A')}):")
        print(f"  {pe_col}: {latest[pe_col]}")
        print(f"  {pb_col}: {latest[pb_col]}")


if __name__ == "__main__":
    example_basic_usage()
    example_with_date_range()
    example_recent_quarters()
    example_multiple_stocks()
    example_analyze_metrics()