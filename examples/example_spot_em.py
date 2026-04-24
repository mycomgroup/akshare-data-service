"""get_spot_em 示例（带空结果重试和降级输出）。"""

import re
import time
from datetime import date, timedelta
from typing import Callable, Optional

import pandas as pd

from akshare_data import get_daily, get_service


def _normalize_symbol(symbol: str) -> str:
    m = re.search(r"(\d{6})", symbol)
    return m.group(1) if m else symbol.strip()


def _fetch_with_retry(fetcher: Callable[[], pd.DataFrame], desc: str) -> Optional[pd.DataFrame]:
    for i in range(3):
        try:
            df = fetcher()
            if df is not None and not df.empty:
                return df
            print(f"{desc}: 第 {i + 1}/3 次返回空结果")
        except Exception as e:  # noqa: BLE001
            print(f"{desc}: 第 {i + 1}/3 次失败 -> {e}")
        time.sleep(1)
    return None


def _candidate_trading_dates(count: int = 5) -> list[str]:
    today = date.today()
    d = today if today.weekday() < 5 else today - timedelta(days=today.weekday() - 4)
    out: list[str] = []
    while len(out) < count:
        if d.weekday() < 5 and d <= today:
            out.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return out


def _get_spot_df(service) -> Optional[pd.DataFrame]:
    attempts: list[tuple[str, Callable[[], pd.DataFrame]]] = [
        ("service.get_spot_em", lambda: service.get_spot_em()),
        ("service.akshare.get_spot_em", lambda: service.akshare.get_spot_em()),
    ]
    # 参数兼容：部分实现可能接受市场参数
    for market in ("A股", "沪深A股", "all"):
        attempts.append(
            (
                f"service.akshare.get_spot_em(market={market})",
                lambda m=market: service.akshare.get_spot_em(market=m),
            )
        )
    for desc, fetcher in attempts:
        df = _fetch_with_retry(fetcher, desc)
        if df is not None and not df.empty:
            return df
    return None


def _fallback_daily_view(symbols: list[str]) -> Optional[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        norm = _normalize_symbol(symbol)
        try:
            df = get_daily(symbol=norm, start_date="", end_date="")
        except Exception:  # noqa: BLE001
            continue
        if df is None or df.empty:
            continue
        one = df.tail(1).copy()
        one["symbol"] = norm
        keep = [c for c in ["symbol", "date", "open", "high", "low", "close", "volume"] if c in one.columns]
        frames.append(one[keep or one.columns])
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    print("=" * 60)
    print("get_spot_em 示例（重试 + 降级）")
    print("=" * 60)

    service = get_service()
    df = _get_spot_df(service)
    if df is None:
        print("最终无数据（可能是非交易时段或数据源异常）")
        print(f"候选交易日回退: {', '.join(_candidate_trading_dates())}")
        fallback = _fallback_daily_view(["600519", "000001", "300750"])
        if fallback is not None and not fallback.empty:
            print("\n降级展示：代表股票最近一日行情")
            print(fallback.to_string(index=False))
        return

    print(f"数据形状: {df.shape}")
    print(f"字段列表: {list(df.columns)}")

    code_col = "代码" if "代码" in df.columns else ("code" if "code" in df.columns else None)
    for symbol in ["600519", "sh600519", "000001.XSHE"]:
        norm = _normalize_symbol(symbol)
        if code_col is None:
            print("无法按 symbol 筛选：未找到代码列")
            break
        hit = df[df[code_col].astype(str) == norm]
        print(f"{symbol} -> {norm}: {'命中' if not hit.empty else '未命中'}")

    if "成交额" in df.columns:
        df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
        print("\n成交额Top5:")
        cols = [c for c in ["代码", "名称", "成交额"] if c in df.columns]
        print(df.nlargest(5, "成交额")[cols].to_string(index=False))
    else:
        print("\n降级输出前10行：")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
