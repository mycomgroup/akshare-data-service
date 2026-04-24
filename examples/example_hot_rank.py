"""get_hot_rank 接口示例（带重试与降级）。

演示如何使用 akshare_data.get_hot_rank() 获取港股热度排行数据。

返回字段包括: 排名、股票代码、股票名称、最新价、涨跌幅等。

注意: 该接口返回港股实时热度排行数据，不支持日期参数。
"""

import logging
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

import pandas as pd

from akshare_data import get_service
from _example_utils import fetch_with_retry


def _mock_hot_rank() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rank": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "symbol": ["00700", "00941", "09988", "03690", "01299", "01810", "02318", "02628", "00388", "00005"],
            "name": ["腾讯控股", "中国移动", "阿里巴巴-SW", "美团-W", "友邦保险", "小米集团-W", "中国平安", "中国人寿", "香港交易所", "汇丰控股"],
            "price": [380.0, 72.5, 85.3, 142.6, 68.9, 18.5, 42.3, 15.8, 285.0, 65.2],
            "pct_change": [2.5, -0.3, 1.8, 0.9, -1.2, 3.2, -0.8, 1.5, 0.6, -0.5],
        }
    )


def _get_hot_rank_df(service) -> pd.DataFrame:
    methods = [
        lambda: service.get_hot_rank(),
        lambda: service.akshare.get_hot_rank(),
    ]
    for fn in methods:
        try:
            df = fetch_with_retry(fn, retries=2)
            if df is not None and not df.empty:
                return df
        except Exception:
            continue
    print("[港股热度排行接口不可用，使用演示数据]")
    return _mock_hot_rank()


def main() -> None:
    print("=" * 60)
    print("get_hot_rank 示例（重试 + 降级）")
    print("=" * 60)

    service = get_service()
    df = _get_hot_rank_df(service)

    print(f"数据形状: {df.shape}")
    print(f"字段列表: {list(df.columns)}")
    print("\n前20行:")
    print(df.head(20).to_string(index=False))

    rank_col = "rank" if "rank" in df.columns else ("排名" if "排名" in df.columns else None)
    if rank_col:
        top10 = df[df[rank_col] <= 10]
        print(f"\nTop10 条数: {len(top10)}")


if __name__ == "__main__":
    main()
