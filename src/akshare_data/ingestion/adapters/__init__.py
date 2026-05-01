"""Adapters package — source adapters for the ingestion layer."""

from akshare_data.ingestion.adapters.akshare import AkShareAdapter
from akshare_data.ingestion.adapters.lixinger import LixingerAdapter
from akshare_data.ingestion.adapters.mock import MockAdapter
from akshare_data.ingestion.adapters.tushare import TushareAdapter

# New adapters from analysis_v2
from akshare_data.ingestion.adapters.eastmoney import EastMoneyAdapter
from akshare_data.ingestion.adapters.efinance import EFinanceAdapter
from akshare_data.ingestion.adapters.baostock import BaoStockAdapter
from akshare_data.ingestion.adapters.tickflow import TickFlowAdapter

__all__ = [
    "AkShareAdapter",
    "LixingerAdapter",
    "MockAdapter",
    "TushareAdapter",
    "EastMoneyAdapter",
    "EFinanceAdapter",
    "BaoStockAdapter",
    "TickFlowAdapter",
]
