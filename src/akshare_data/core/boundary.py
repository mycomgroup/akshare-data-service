from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Optional, Any
import pandas as pd

class IOnlineDataReader(ABC):
    """在线服务只读数据接口，在线模块仅通过此接口访问数据"""
    
    @abstractmethod
    def query(self, table: str, symbols: Optional[List[str]] = None, 
              start_date: Optional[date] = None, end_date: Optional[date] = None,
              filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """查询数据，仅支持读操作"""
        pass
    
    @abstractmethod
    def exists(self, table: str, symbols: Optional[List[str]] = None,
               start_date: Optional[date] = None, end_date: Optional[date] = None) -> bool:
        """检查指定数据是否存在"""
        pass
    
    @abstractmethod
    def get_metadata(self, table: str) -> Dict[str, Any]:
        """获取表元数据"""
        pass

class IOfflineDataWriter(ABC):
    """离线任务只写数据接口，离线模块仅通过此接口写入数据"""
    
    @abstractmethod
    def write(self, table: str, data: pd.DataFrame, overwrite: bool = False) -> int:
        """写入数据，返回写入行数"""
        pass
    
    @abstractmethod
    def delete(self, table: str, symbols: Optional[List[str]] = None,
               start_date: Optional[date] = None, end_date: Optional[date] = None) -> int:
        """删除指定范围数据，返回删除行数"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交写入操作，触发在线服务增量加载"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """回滚未提交的写入操作"""
        pass
