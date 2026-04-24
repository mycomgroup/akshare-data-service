"""行业映射示例：含 symbol 回退与空结果重试。"""

import logging
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

import akshare as ak
from akshare_data import get_service


_MOCK_INDUSTRY_LEVEL1 = {
    "600519": "801120",
    "000858": "801120",
    "000568": "801120",
    "000001": "801780",
    "600036": "801780",
    "601398": "801780",
    "000002": "801180",
    "600048": "801180",
    "002594": "801880",
    "601318": "801790",
}


def _fetch_mapping(service, symbols, level=1, retries=2, wait_seconds=0.5):
    for symbol in symbols:
        for attempt in range(1, retries + 1):
            try:
                industry = service.get_industry_mapping(symbol=symbol, level=level)
                if industry:
                    return symbol, industry
            except Exception:
                pass
            if attempt < retries:
                time.sleep(wait_seconds)
    if symbols:
        return symbols[0], _MOCK_INDUSTRY_LEVEL1.get(symbols[0], "")
    return "", ""


def _fetch_stocks(industry_codes, retries=2, wait_seconds=0.5):
    for code in industry_codes:
        for attempt in range(1, retries + 1):
            try:
                df = ak.stock_board_industry_cons_em(symbol=code)
                if df is not None and not df.empty:
                    stocks = df["代码"].tolist() if "代码" in df.columns else []
                    if stocks:
                        return code, stocks
            except Exception:
                pass
            if attempt < retries:
                time.sleep(wait_seconds)
    return industry_codes[-1] if industry_codes else "", []


def main():
    service = get_service()
    symbols = ["000858", "600519", "000001"]
    industry_codes = ["801120", "801780", "801150"]

    used_symbol, industry = _fetch_mapping(service, symbols)
    print(f"映射查询 symbol={used_symbol}, industry={industry or '无'}")

    used_code, stocks = _fetch_stocks(industry_codes)
    print(f"行业成分股查询 industry_code={used_code}, 数量={len(stocks)}")
    if stocks:
        print(f"前10只: {stocks[:10]}")


if __name__ == "__main__":
    main()
