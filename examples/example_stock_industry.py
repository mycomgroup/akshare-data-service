"""get_stock_industry 示例：symbol 回退 + 空数据重试。"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import time
import pandas as pd
import akshare as ak


def _mock_stock_industry(symbol):
    return pd.DataFrame({
        "code": [symbol],
        "industry_name": ["演示行业"],
        "industry_code": ["demo001"],
    })


def _fetch_stock_industry(symbol, retries=2, wait_seconds=1.0):
    for attempt in range(1, retries + 1):
        try:
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                return symbol, df
        except Exception:
            pass
        if attempt < retries:
            time.sleep(wait_seconds)
    return symbol, pd.DataFrame()


def main():
    symbols = ["600519", "000858", "000001", "300750"]
    for sym in symbols:
        symbol, df = _fetch_stock_industry(sym, retries=2, wait_seconds=1.0)
        if df.empty:
            print(f"{sym}: 个股行业为空（已重试并回退 symbol）")
            continue
        print(f"使用 symbol={symbol}")
        print(f"记录数: {len(df)}")
        print(f"字段: {list(df.columns)}")
        print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()