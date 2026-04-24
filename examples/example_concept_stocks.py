"""get_concept_stocks 示例：先获取概念列表再查询成分股。"""

import logging
import warnings
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

from akshare_data import get_service
from _example_utils import fetch_with_retry, is_empty_result


def main():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        service = get_service()

    concept_list = fetch_with_retry(lambda: service.get_concept_list())
    if is_empty_result(concept_list):
        print("概念列表为空（网络可能不可用）")
        return

    fallback_codes = [
        row["concept_code"]
        for _, row in concept_list.head(10).iterrows()
        if "concept_code" in concept_list.columns
    ]
    if not fallback_codes:
        print("无法获取有效的概念代码")
        return

    used_code = None
    df = pd.DataFrame()
    for code in fallback_codes:
        result = fetch_with_retry(lambda c=code: service.get_concept_stocks(concept_code=c))
        if not is_empty_result(result):
            used_code = code
            df = result
            break

    if df.empty:
        print("概念成分股为空（已重试并回退概念代码）")
        return

    concept_name = ""
    if "concept_code" in concept_list.columns and "concept_name" in concept_list.columns:
        match = concept_list[concept_list["concept_code"] == used_code]
        if not match.empty:
            concept_name = match.iloc[0].get("concept_name", "")

    print(f"使用概念: {used_code}" + (f" ({concept_name})" if concept_name else ""))
    print(f"成分股数量: {len(df)}")
    print(f"字段: {list(df.columns)}")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()