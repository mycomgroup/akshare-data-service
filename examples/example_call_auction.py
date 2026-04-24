"""
集合竞价接口示例 (get_call_auction)

演示如何获取A股集合竞价阶段的逐笔成交数据。
可用于分析开盘集合竞价的量价特征、主力动向等场景。

导入方式: from akshare_data import get_call_auction
"""

import logging
from datetime import date, timedelta

from akshare_data import get_call_auction, get_daily

logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _candidate_fallback_dates(count: int = 5) -> list[str]:
    today = date.today()
    d = today if today.weekday() < 5 else today - timedelta(days=today.weekday() - 4)
    out: list[str] = []
    while len(out) < count:
        if d.weekday() < 5 and d <= today:
            out.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return out


def _normalize_symbol_variants(symbol: str) -> list[str]:
    raw = str(symbol).strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    variants = [raw]
    if len(digits) == 6:
        variants.extend([digits, f"sh{digits}", f"sz{digits}"])
    # 去重并保持顺序，兼容不同后端对 symbol 格式的要求
    return list(dict.fromkeys([v for v in variants if v]))


def _normalize_date_variants(value: str | None) -> list[str | None]:
    if value is None:
        return [None]
    text = str(value).strip()
    if not text:
        return [None]
    compact = text.replace("-", "")
    variants: list[str | None] = [text]
    if len(compact) == 8 and compact.isdigit():
        variants.append(compact)
        variants.append(f"{compact[:4]}-{compact[4:6]}-{compact[6:8]}")
    variants.append(None)
    return list(dict.fromkeys(variants))


def _safe_fetch_call_auction(symbol: str, dt: str | None):
    try:
        return get_call_auction(symbol=symbol, date=dt)
    except Exception:  # noqa: BLE001
        return None


def _fetch_call_auction_with_fallback(symbol: str, target_date: str | None = None):
    base_dates = [target_date] if target_date else _candidate_fallback_dates()
    attempted: list[tuple[str, str | None]] = []
    for d in base_dates:
        for dt in _normalize_date_variants(d):
            for sym in _normalize_symbol_variants(symbol):
                attempted.append((sym, dt))
                df = _safe_fetch_call_auction(sym, dt)
                if df is not None and not df.empty:
                    return df, {"symbol": sym, "date": dt, "attempted": attempted}
    return None, {"symbol": symbol, "date": None, "attempted": attempted}


def _fallback_daily_snapshot(symbol: str):
    for sym in _normalize_symbol_variants(symbol):
        try:
            df = get_daily(symbol=sym, start_date="", end_date="")
            if df is not None and not df.empty:
                cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
                return df.tail(5)[cols or df.columns[:6]]
        except Exception:  # noqa: BLE001
            continue
    return None


def example_basic_usage():
    """基本用法: 获取单只股票的集合竞价数据"""
    print("=" * 60)
    print("示例1: 获取单只股票集合竞价数据")
    print("=" * 60)

    try:
        df, meta = _fetch_call_auction_with_fallback(symbol="600519")

        if df is None or df.empty:
            print("集合竞价无数据（可能是接口不可用或非交易阶段）")
            print(f"候选回退日期: {', '.join(_candidate_fallback_dates())}")
            fallback_df = _fallback_daily_snapshot("600519")
            if fallback_df is not None and not fallback_df.empty:
                print("\n降级展示：最近5个交易日行情摘要")
                print(fallback_df)
            return
        print(f"命中参数: symbol={meta['symbol']} date={meta['date']}")

        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")

        print("\n前10行数据:")
        print(df.head(10))

    except Exception as e:
        print(f"获取集合竞价数据失败: {e}")


def example_multiple_symbols():
    """多只股票: 获取多只股票的集合竞价数据"""
    print("\n" + "=" * 60)
    print("示例2: 获取多只股票集合竞价数据")
    print("=" * 60)

    symbols = ["600519", "000001", "300750"]  # 贵州茅台、平安银行、宁德时代

    for sym in symbols:
        try:
            df, meta = _fetch_call_auction_with_fallback(symbol=sym)
            if df is not None and not df.empty:
                print(f"\n{sym}: {df.shape[0]} 条记录 (symbol={meta['symbol']} date={meta['date']})")
                print(df.head(3))
            else:
                print(f"\n{sym}: 集合竞价无数据")
                print(f"候选回退日期: {', '.join(_candidate_fallback_dates())}")
                fallback_df = _fallback_daily_snapshot(sym)
                if fallback_df is not None and not fallback_df.empty:
                    print("降级展示：最近3行日线摘要")
                    print(fallback_df.tail(3))
        except Exception as e:
            print(f"\n{sym}: 获取失败 - {e}")


def example_with_date():
    """指定日期: 获取特定日期的集合竞价数据"""
    print("\n" + "=" * 60)
    print("示例3: 指定日期的集合竞价数据")
    print("=" * 60)

    try:
        target_date = _candidate_fallback_dates(count=1)[0]
        df, meta = _fetch_call_auction_with_fallback(symbol="600519", target_date=target_date)

        if df is None or df.empty:
            print("无数据（指定日期可能无交易）")
            print(f"候选回退日期: {', '.join(_candidate_fallback_dates())}")
            fallback_df = _fallback_daily_snapshot("600519")
            if fallback_df is not None and not fallback_df.empty:
                print("\n降级展示：最近5个交易日行情摘要")
                print(fallback_df)
            return

        print(f"命中参数: symbol={meta['symbol']} date={meta['date']}")
        print(f"数据形状: {df.shape}")
        print("\n数据预览:")
        print(df.head(10))

    except Exception as e:
        print(f"获取集合竞价数据失败: {e}")


def example_analysis():
    """分析: 集合竞价量价分析"""
    print("\n" + "=" * 60)
    print("示例4: 集合竞价量价分析")
    print("=" * 60)

    try:
        df, meta = _fetch_call_auction_with_fallback(symbol="600519")

        if df is None or df.empty:
            print("集合竞价无数据")
            print(f"候选回退日期: {', '.join(_candidate_fallback_dates())}")
            fallback_df = _fallback_daily_snapshot("600519")
            if fallback_df is not None and not fallback_df.empty:
                print("\n降级展示：最近5个交易日行情摘要")
                print(fallback_df)
            return

        print(f"命中参数: symbol={meta['symbol']} date={meta['date']}")
        print(f"总记录数: {len(df)}")

        # 统计成交量/额字段
        vol_cols = [c for c in df.columns if 'vol' in c.lower() or '量' in c]
        price_cols = [c for c in df.columns if 'price' in c.lower() or '价' in c or 'close' in c.lower()]
        amount_cols = [c for c in df.columns if 'amount' in c.lower() or '额' in c]

        if vol_cols:
            print(f"\n成交量列: {vol_cols}")
        if price_cols:
            print(f"价格列: {price_cols}")
        if amount_cols:
            print(f"成交额列: {amount_cols}")

        print("\n描述统计:")
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"分析失败: {e}")


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_symbols()
    example_with_date()
    example_analysis()
