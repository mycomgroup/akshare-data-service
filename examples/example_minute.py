"""
get_minute() 接口示例

演示如何使用 akshare_data.get_minute() 获取股票分钟级行情数据。

支持频率:
  - "1min": 1分钟线 (默认)
  - "5min": 5分钟线
  - "15min": 15分钟线
  - "30min": 30分钟线
  - "60min": 60分钟线

日期参数 (start_date/end_date) 为可选:
  - 不传: 返回缓存中的全部分钟数据
  - 传入: 获取指定日期范围的数据

返回字段: symbol, datetime, open, high, low, close, volume, amount
"""

import logging
import warnings
from datetime import date, timedelta

import pandas as pd
from akshare_data import get_minute

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _last_trading_day(anchor: date | None = None) -> date:
    d = min(anchor or date.today(), date.today())
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _date_range(days: int = 3) -> tuple[str, str]:
    end = _last_trading_day()
    start = end - timedelta(days=max(days * 2, 3))
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _candidate_fallback_dates(count: int = 5) -> list[str]:
    d = _last_trading_day()
    out: list[str] = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return out


def _symbol_candidates(symbol: str) -> list[str]:
    s = str(symbol).strip()
    if not s:
        return []
    candidates = [s]

    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) == 6:
        if digits.startswith(("6", "9")):
            candidates.extend([digits, f"sh{digits}", f"{digits}.XSHG"])
        else:
            candidates.extend([digits, f"sz{digits}", f"{digits}.XSHE"])
    # 去重且保持顺序
    return list(dict.fromkeys(candidates))


def _normalize_minute_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    aliases = {
        "symbol": ("symbol", "代码", "证券代码", "股票代码"),
        "datetime": ("datetime", "日期时间", "时间", "date", "trade_time"),
        "open": ("open", "开盘", "open_price"),
        "high": ("high", "最高", "high_price"),
        "low": ("low", "最低", "low_price"),
        "close": ("close", "收盘", "close_price", "最新价"),
        "volume": ("volume", "成交量", "vol", "成交手"),
        "amount": ("amount", "成交额", "turnover", "成交金额"),
    }
    for target, names in aliases.items():
        for name in names:
            if name in df.columns:
                rename_map[name] = target
                break
    out = df.rename(columns=rename_map).copy()
    if "datetime" in out.columns:
        out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
    if "symbol" not in out.columns and "code" in out.columns:
        out["symbol"] = out["code"]
    return out


def _fetch_minute_once(symbol: str, freq: str, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    try:
        df = get_minute(symbol, freq=freq, start_date=start_date, end_date=end_date)
    except Exception as exc:  # pragma: no cover - example script best-effort
        print(f"  [失败] symbol={symbol}, range={start_date}~{end_date}, err={exc}")
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    return _normalize_minute_columns(df)


def _get_minute(symbol, freq="1min", start_date=None, end_date=None):
    """分钟数据拉取：symbol 候选 + 日期范围回退 + 字段兼容。"""
    symbols = _symbol_candidates(symbol) if isinstance(symbol, str) else []
    if not symbols and isinstance(symbol, list):
        for s in symbol:
            symbols.extend(_symbol_candidates(str(s)))
        symbols = list(dict.fromkeys(symbols))
    if not symbols:
        print("  [无效参数] 未提供有效 symbol")
        return pd.DataFrame()

    tried = 0
    # 优先尝试用户提供的日期范围
    for sym in symbols:
        df = _fetch_minute_once(sym, freq=freq, start_date=start_date, end_date=end_date)
        tried += 1
        if not df.empty:
            print(f"  [命中] symbol={sym}, range={start_date}~{end_date}, rows={len(df)}")
            return df

    # 自动回退到最近交易日，逐日尝试
    for d in _candidate_fallback_dates(8):
        for sym in symbols:
            df = _fetch_minute_once(sym, freq=freq, start_date=d, end_date=d)
            tried += 1
            if not df.empty:
                print(f"  [回退命中] symbol={sym}, trade_date={d}, rows={len(df)}")
                return df

    print(f"  [无数据] 候选symbol均未命中，尝试次数={tried}")
    print(f"  symbol候选: {', '.join(symbols)}")
    print(f"  候选回退日期: {', '.join(_candidate_fallback_dates())}")
    return pd.DataFrame()


# ============================================================
# 示例 1: 基本用法 - 获取1分钟线数据
# ============================================================
def example_basic():
    """基本用法: 获取指定日期范围的1分钟线数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取1分钟线数据")
    print("=" * 60)

    try:
        start, end = _date_range(5)
        df = _get_minute(symbol=["000001", "600000", "300750"], freq="1min", start_date=start, end_date=end)

        # 打印数据形状
        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        # 打印前几行
        if not df.empty:
            print("\n前5行数据:")
            print(df.head())

            # 打印时间范围
            print(f"\n时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
        else:
            print("\n无数据 (该日期范围可能无分钟数据)")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 不同频率对比
# ============================================================
def example_freq_types():
    """演示不同频率的分钟线数据"""
    print("\n" + "=" * 60)
    print("示例 2: 不同频率对比")
    print("=" * 60)

    symbol = "600519"  # 贵州茅台
    start, end = _date_range(3)

    freqs = ["1min", "5min", "15min", "30min", "60min"]

    for freq in freqs:
        try:
            df = _get_minute(symbol, freq=freq, start_date=start, end_date=end)
            if not df.empty:
                print(
                    f"频率: {freq:8s} -> 数据行数: {len(df):5d}, 时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}"
                )
            else:
                print(f"频率: {freq:8s} -> 无数据")
        except Exception as e:
            print(f"频率: {freq:8s} -> 获取失败: {e}")


# ============================================================
# 示例 3: 不指定日期范围 (获取缓存数据)
# ============================================================
def example_no_dates():
    """不指定日期范围，返回缓存中该股票的全部分钟数据"""
    print("\n" + "=" * 60)
    print("示例 3: 不指定日期范围")
    print("=" * 60)

    try:
        # 不传 start_date 和 end_date，返回缓存中的全部数据
        start, end = _date_range(5)
        df = _get_minute(["000001", "600000"], freq="5min", start_date=start, end_date=end)

        if df is not None and not df.empty:
            print(f"数据形状: {df.shape}")
            print(f"时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
            print("\n前5行:")
            print(df.head())
        else:
            print("无数据（指定范围内未返回分钟线）")
            print(f"候选回退日期: {', '.join(_candidate_fallback_dates())}")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 深市股票分钟线
# ============================================================
def example_sz_stock():
    """获取深市股票的分钟线数据"""
    print("\n" + "=" * 60)
    print("示例 4: 深市股票分钟线 (万科A)")
    print("=" * 60)

    try:
        start, end = _date_range(8)
        df = _get_minute(symbol=["sz000002", "000002", "600036"], freq="15min", start_date=start, end_date=end)

        if not df.empty:
            print(f"数据形状: {df.shape}")
            print("\n基本统计信息:")
            print(df[["open", "high", "low", "close", "volume"]].describe())
        else:
            print("无数据")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 5: 数据分析 - 日内成交量分布
# ============================================================
def example_analysis():
    """演示获取分钟数据后进行日内分析"""
    print("\n" + "=" * 60)
    print("示例 5: 数据分析 - 日内成交量分布")
    print("=" * 60)

    try:
        start, end = _date_range(1)
        df = _get_minute(symbol=["600036", "sh600036"], freq="5min", start_date=start, end_date=end)

        if df.empty:
            print("无数据")
            return

        # 提取时间部分
        df["time"] = pd.to_datetime(df["datetime"]).dt.time

        # 按时间统计平均成交量
        time_volume = df.groupby("time")["volume"].mean().sort_index()

        print("招商银行 2024-06-03 5分钟线")
        print(f"数据行数: {len(df)}")
        print("\n各时段平均成交量:")
        print(time_volume.to_string())

        # 找出成交量最大的时段
        max_time = time_volume.idxmax()
        max_vol = time_volume.max()
        print(f"\n成交量最大时段: {max_time}, 平均成交量: {max_vol:.0f}")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 6: 多种代码格式
# ============================================================
def example_symbol_formats():
    """演示分钟线支持的不同代码格式"""
    print("\n" + "=" * 60)
    print("示例 6: 不同证券代码格式")
    print("=" * 60)

    symbols = [
        "600000",
        "sh600000",
        "600000.XSHG",
    ]

    for sym in symbols:
        try:
            start, end = _date_range(1)
            df = _get_minute(sym, freq="30min", start_date=start, end_date=end)
            if not df.empty:
                print(
                    f"代码格式: {sym:15s} -> 标准化后: {df['symbol'].iloc[0]:10s}, 行数: {len(df)}"
                )
            else:
                print(f"代码格式: {sym:15s} -> 无数据")
        except Exception as e:
            print(f"代码格式: {sym:15s} -> 获取失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_freq_types()
    example_no_dates()
    example_sz_stock()
    example_analysis()
    example_symbol_formats()
