"""Thin compatibility wrapper for the online read-only API.

Business logic is split into:
- `service_facade.py`: read/query/backfill facade delegating to Served DataService
- `legacy_adapter.py`: legacy source compatibility proxies/warnings
- `namespace_assembly.py`: market namespace assembly (cn/hk/us/macro)

Online API does not synchronously fetch from source adapters and does not write
cache data.
"""

from akshare_data.legacy_adapter import SourceProxy
from akshare_data.namespace_assembly import (
    CNETFQuoteAPI,
    CNIndexMetaAPI,
    CNIndexQuoteAPI,
    CNMarketAPI,
    CNStockCapitalAPI,
    CNStockEventAPI,
    CNStockFinanceAPI,
    CNStockQuoteAPI,
    HKMarketAPI,
    HKStockQuoteAPI,
    MacroAPI,
    MacroChinaAPI,
    USMarketAPI,
    USStockQuoteAPI,
)
from akshare_data.service_facade import DataService, get_service

__all__ = [
    "DataService",
    "get_service",
    "SourceProxy",
    "CNStockQuoteAPI",
    "CNStockFinanceAPI",
    "CNStockCapitalAPI",
    "CNIndexQuoteAPI",
    "CNIndexMetaAPI",
    "CNETFQuoteAPI",
    "CNStockEventAPI",
    "HKStockQuoteAPI",
    "HKMarketAPI",
    "USStockQuoteAPI",
    "USMarketAPI",
    "MacroChinaAPI",
    "MacroAPI",
    "CNMarketAPI",
]
