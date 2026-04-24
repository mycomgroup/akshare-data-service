"""
集合竞价/五档行情接口示例

注意: call_auction 接口目前在配置中已禁用 (enabled: false)，
因为 AkShare 暂无稳定的集合竞价数据接口。
本示例演示如何使用 get_spot_em (实时行情) 数据作为替代。

运行建议: python -W ignore example_call_auction.py

导入方式: from akshare_data import get_service
"""

import logging
import sys
import warnings

<<<<<<< HEAD
if not sys.warnoptions:
    warnings.simplefilter("ignore")
    sys.warnoptions = ["ignore"]
=======
from akshare_data import get_call_auction, get_daily
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

logging.getLogger("akshare_data").setLevel(logging.CRITICAL)
logging.getLogger("ServedReader").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

from datetime import datetime, timedelta

from akshare_data import get_service


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


<<<<<<< HEAD
def _fetch_spot_data(service, retries: int = 2):
    """获取实时行情数据（带重试）"""
    import time
    for i in range(retries):
        try:
            df = service.get_spot_em()
            if df is not None and not df.empty:
                return df
            print(f"第 {i + 1}/{retries} 次: 返回空数据")
        except Exception as e:
            print(f"第 {i + 1}/{retries} 次失败: {e}")
        time.sleep(0.5)
    return None


def _fetch_spot_via_akshare(retries: int = 2):
    """直接通过 akshare 获取实时行情（绕过 DataService）"""
    import time
    for i in range(retries):
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                return df
            print(f"akshare 第 {i + 1}/{retries} 次: 返回空数据")
        except Exception as e:
            print(f"akshare 第 {i + 1}/{retries} 次失败: {e}")
        time.sleep(0.5)
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
    return None


def example_basic_usage():
    """基本用法: 获取单只股票的实时行情数据"""
    print("=" * 60)
    print("示例1: 获取单只股票实时行情数据")
    print("=" * 60)
    print("注意: call_auction 接口已禁用，使用 get_spot_em 替代")
    print()

<<<<<<< HEAD
    service = get_service()
    df = _fetch_spot_data(service)
    
    if df is None or df.empty:
        print("DataService 返回空数据，尝试直接调用 akshare...")
        df = _fetch_spot_via_akshare()

    if df is None or df.empty:
        print("无数据（可能是非交易时间或数据源异常）")
        return
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")

    code_col = None
    for col in ["代码", "code", "symbol"]:
        if col in df.columns:
            code_col = col
            break

    if code_col:
        import re
        symbol = "600519"
        m = re.search(r"(\d{6})", symbol)
        norm = m.group(1) if m else symbol.strip()
        hit = df[df[code_col].astype(str) == norm]
        if not hit.empty:
            print(f"\n股票 {symbol} 数据:")
            print(hit.to_string(index=False))
        else:
            print(f"\n未找到股票 {symbol}")
            print("\n前5行数据示例:")
            print(df.head(5).to_string(index=False))
    else:
        print("\n前5行数据示例:")
        print(df.head(5).to_string(index=False))


def example_multiple_symbols():
    """多只股票: 获取多只股票的实时行情数据"""
    print("\n" + "=" * 60)
    print("示例2: 获取多只股票实时行情数据")
    print("=" * 60)

    symbols = ["600519", "000001", "300750"]

    service = get_service()
    df = _fetch_spot_data(service)
    
    if df is None or df.empty:
        print("DataService 返回空数据，尝试直接调用 akshare...")
        df = _fetch_spot_via_akshare()

    if df is None or df.empty:
        print("无数据（可能是非交易时间或数据源异常）")
        return

    code_col = None
    for col in ["代码", "code", "symbol"]:
        if col in df.columns:
            code_col = col
            break

    if code_col is None:
        print("未找到代码列")
        return

    import re
    for sym in symbols:
<<<<<<< HEAD
        m = re.search(r"(\d{6})", sym)
        norm = m.group(1) if m else sym.strip()
        hit = df[df[code_col].astype(str) == norm]
        if not hit.empty:
            print(f"\n{sym}: 找到数据")
            display_cols = [c for c in ["代码", "名称", "最新价", "涨跌幅", "成交量", "成交额"] if c in hit.columns]
            print(hit[display_cols].to_string(index=False) if display_cols else hit.to_string(index=False))
        else:
            print(f"\n{sym}: 未找到数据")
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d


def example_with_fields():
    """字段分析: 展示实时行情的主要字段"""
    print("\n" + "=" * 60)
    print("示例3: 实时行情字段分析")
    print("=" * 60)

<<<<<<< HEAD
    service = get_service()
    df = _fetch_spot_data(service)
    
    if df is None or df.empty:
        print("DataService 返回空数据，尝试直接调用 akshare...")
        df = _fetch_spot_via_akshare()

    if df is None or df.empty:
        print("无数据")
        return

    print(f"总股票数: {len(df)}")
    print(f"字段列表: {list(df.columns)}")
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

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


def example_top_stocks():
    """排行榜: 按成交额排序"""
    print("\n" + "=" * 60)
    print("示例4: 按成交额排序的 Top 股票")
    print("=" * 60)

<<<<<<< HEAD
    service = get_service()
    df = _fetch_spot_data(service)
    
    if df is None or df.empty:
        print("DataService 返回空数据，尝试直接调用 akshare...")
        df = _fetch_spot_via_akshare()

    if df is None or df.empty:
        print("无数据")
        return

    amount_col = None
    for col in ["成交额", "amount", "amounts"]:
        if col in df.columns:
            amount_col = col
            break
=======
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
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

    if amount_col is None:
        print("未找到成交额列")
        return

    import pandas as pd
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
    top = df.nlargest(10, amount_col)

    display_cols = [c for c in ["代码", "名称", amount_col, "涨跌幅"] if c in top.columns]
    print(f"\n成交额 Top 10:")
    print(top[display_cols].to_string(index=False))


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_symbols()
    example_with_fields()
    example_top_stocks()