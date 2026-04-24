"""get_concept_list 示例：空数据重试 + 直接 akshare 回退。"""

import logging
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import akshare as ak

logging.getLogger("akshare_data").setLevel(logging.ERROR)

from akshare_data import get_service
from _example_utils import fetch_with_retry, is_empty_result


def _fetch_from_service():
    """通过 DataService 获取概念列表。"""
    try:
        service = get_service()
        return service.get_concept_list()
    except Exception:
        return pd.DataFrame()


def _fetch_from_akshare_direct():
    """直接调用 akshare 获取概念列表。"""
    try:
        return ak.stock_board_concept_name_em()
    except Exception:
        return pd.DataFrame()


def _sample_concept_list():
    """样本数据回退。"""
    return pd.DataFrame([
        {"concept_code": "BK0001", "concept_name": "区块链"},
        {"concept_code": "BK0002", "concept_name": "人工智能"},
        {"concept_code": "BK0003", "concept_name": "新能源汽车"},
        {"concept_code": "BK0004", "concept_name": "芯片"},
        {"concept_code": "BK0005", "concept_name": "机器人"},
    ])


def main():
    # 1. 尝试通过 DataService 获取
    df = fetch_with_retry(_fetch_from_service, retries=2)
    source = "DataService"

    # 2. 如果为空，尝试直接调用 akshare
    if is_empty_result(df):
        df = fetch_with_retry(_fetch_from_akshare_direct, retries=2)
        source = "akshare"

    # 3. 如果仍为空，使用样本数据
    if is_empty_result(df):
        df = _sample_concept_list()
        source = "sample"
        print("网络不可用，使用样本数据展示格式")

    print(f"数据来源: {source}")
    print(f"概念数量: {len(df)}")
    print(f"字段: {list(df.columns)}")
    print(df.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
