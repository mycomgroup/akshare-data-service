"""get_sw_industry_daily 示例：index_code/date 回退 + 空数据重试。"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime, timedelta

import pandas as pd

warnings.filterwarnings("ignore")
logging.getLogger("akshare_data").setLevel(logging.ERROR)

import akshare as ak


def _is_empty_result(value) -> bool:
    """Check whether value should be treated as empty."""
    if value is None:
        return True
    if hasattr(value, "empty"):
        return bool(value.empty)
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) == 0
    return False


def _fetch_with_retry(fetcher, retries: int = 2, sleep_seconds: float = 0.6):
    """Retry on empty value or exception, return last value."""
    import time

    last_value = None
    last_error = None
    for idx in range(retries + 1):
        try:
            value = fetcher()
            last_value = value
            if not _is_empty_result(value):
                return value
        except Exception as exc:
            last_error = exc
        if idx < retries:
            time.sleep(sleep_seconds)
    if last_error is not None and _is_empty_result(last_value):
        raise last_error
    return last_value


def _fetch_sw_daily_with_fallback(
    index_codes: list[str],
    start_date: str,
    end_date: str,
    retries: int = 2,
) -> tuple[str | None, str, str, pd.DataFrame]:
    """Fetch SW industry daily with retry and symbol fallback."""
    for code in index_codes:
        try:
            df = _fetch_with_retry(
                lambda c=code: ak.stock_board_industry_hist_em(
                    symbol=c,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                ),
                retries=retries,
            )
            if not _is_empty_result(df):
                return code, start_date, end_date, df
        except Exception:
            continue
    return None, start_date, end_date, pd.DataFrame()


def main():
    index_codes = ["801120", "801080", "801780", "801150"]
    today = datetime.now().date()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")

    print(f"尝试获取申万行业日线数据: {start_date} ~ {end_date}")
    code, s_date, e_date, df = _fetch_sw_daily_with_fallback(
        index_codes, start_date, end_date
    )

    if df.empty:
        print("申万行业日线为空（已重试并回退 index_code）")
        return

    print(f"使用参数: index_code={code}, start_date={s_date}, end_date={e_date}")
    print(f"记录数: {len(df)}")
    print(f"字段: {list(df.columns)}")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()