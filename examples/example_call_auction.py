"""
集合竞价/五档行情接口示例

注意: call_auction 接口目前在配置中已禁用 (enabled: false)，
因为 AkShare 暂无稳定的集合竞价数据接口。
本示例演示如何使用 bid_ask (五档买卖盘) 数据作为替代。

导入方式: from akshare_data import get_service
"""

import warnings
from datetime import datetime, timedelta

from akshare_data import get_service

warnings.filterwarnings("ignore", category=DeprecationWarning)


def _last_trading_day(anchor: datetime | None = None) -> datetime:
    """回退到最近工作日（避免周末和未来日）"""
    today = datetime.now()
    d = min(anchor or today, today)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _candidate_dates(count: int = 5) -> list[str]:
    """生成候选日期列表"""
    d = _last_trading_day()
    out: list[str] = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return out


def _fetch_bid_ask_with_retry(service, symbol: str, retries: int = 3):
    """获取五档数据（带重试）"""
    for i in range(retries):
        try:
            df = service.get_spot_em()
            if df is not None and not df.empty:
                code_col = None
                for col in ["代码", "code", "symbol"]:
                    if col in df.columns:
                        code_col = col
                        break
                if code_col:
                    import re
                    m = re.search(r"(\d{6})", symbol)
                    norm = m.group(1) if m else symbol.strip()
                    hit = df[df[code_col].astype(str) == norm]
                    if not hit.empty:
                        return hit, None
            print(f"第 {i + 1}/{retries} 次: 未找到 {symbol} 数据")
        except Exception as e:
            print(f"第 {i + 1}/{retries} 次失败: {e}")
        import time
        time.sleep(1)
    return None, None


def example_basic_usage():
    """基本用法: 获取单只股票的五档行情数据"""
    print("=" * 60)
    print("示例1: 获取单只股票五档行情数据")
    print("=" * 60)
    print("注意: call_auction 接口已禁用，使用 get_spot_em 替代")
    print()

    try:
        service = get_service()
        df, _ = _fetch_bid_ask_with_retry(service, symbol="600519")

        if df is None or df.empty:
            print("无数据（可能是非交易时间或数据不可用）")
            return

        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")

        print("\n数据内容:")
        print(df.to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


def example_multiple_symbols():
    """多只股票: 获取多只股票的五档行情数据"""
    print("\n" + "=" * 60)
    print("示例2: 获取多只股票五档行情数据")
    print("=" * 60)

    symbols = ["600519", "000001", "300750"]

    try:
        service = get_service()
        all_df = service.get_spot_em()

        if all_df is None or all_df.empty:
            print("无数据（可能是非交易时间或数据不可用）")
            return

        code_col = None
        for col in ["代码", "code", "symbol"]:
            if col in all_df.columns:
                code_col = col
                break

        if code_col is None:
            print("未找到代码列")
            return

        import re
        for sym in symbols:
            m = re.search(r"(\d{6})", sym)
            norm = m.group(1) if m else sym.strip()
            hit = all_df[all_df[code_col].astype(str) == norm]
            if not hit.empty:
                print(f"\n{sym}: 找到 {len(hit)} 条记录")
                print(hit.to_string(index=False))
            else:
                print(f"\n{sym}: 未找到数据")

    except Exception as e:
        print(f"获取数据失败: {e}")


def example_with_fields():
    """字段分析: 展示五档行情的主要字段"""
    print("\n" + "=" * 60)
    print("示例3: 五档行情字段分析")
    print("=" * 60)

    try:
        service = get_service()
        df = service.get_spot_em()

        if df is None or df.empty:
            print("无数据")
            return

        print(f"总股票数: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        vol_cols = [c for c in df.columns if "量" in c or "vol" in c.lower()]
        price_cols = [c for c in df.columns if "价" in c or "price" in c.lower()]
        amount_cols = [c for c in df.columns if "额" in c or "amount" in c.lower()]

        if vol_cols:
            print(f"\n成交量相关列: {vol_cols}")
        if price_cols:
            print(f"价格相关列: {price_cols}")
        if amount_cols:
            print(f"成交额相关列: {amount_cols}")

        print("\n数据示例 (前5行):")
        print(df.head(5).to_string(index=False))

    except Exception as e:
        print(f"分析失败: {e}")


def example_top_stocks():
    """排行榜: 按成交额排序"""
    print("\n" + "=" * 60)
    print("示例4: 按成交额排序的 Top 股票")
    print("=" * 60)

    try:
        service = get_service()
        df = service.get_spot_em()

        if df is None or df.empty:
            print("无数据")
            return

        amount_col = None
        for col in ["成交额", "amount", "amounts"]:
            if col in df.columns:
                amount_col = col
                break

        if amount_col is None:
            print("未找到成交额列")
            return

        import pandas as pd
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
        top = df.nlargest(10, amount_col)

        display_cols = [c for c in ["代码", "名称", amount_col, "涨跌幅"] if c in top.columns]
        print(f"\n成交额 Top 10:")
        print(top[display_cols].to_string(index=False))

    except Exception as e:
        print(f"获取排行榜失败: {e}")


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_symbols()
    example_with_fields()
    example_top_stocks()