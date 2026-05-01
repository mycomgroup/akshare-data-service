import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
from .cache_manager import CacheManager
from ..core.boundary import IOnlineDataReader, IOfflineDataWriter
from ..core.exceptions import WriteConflictError

class IsolationLayer(IOnlineDataReader, IOfflineDataWriter):
    """数据隔离层，实现读写分离和事务性写入"""
    
    def __init__(self, cache_dir: str, cache_manager: CacheManager):
        self.cache_dir = Path(cache_dir)
        self.cache_manager = cache_manager
        self.tmp_dir = self.cache_dir / ".tmp" / f"write_{os.getpid()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.pending_writes: Dict[str, List[pd.DataFrame]] = {}
        self.current_version = self._load_current_version()
    
    def _load_current_version(self) -> int:
        """加载当前数据版本号"""
        version_file = self.cache_dir / "version"
        if version_file.exists():
            return int(version_file.read_text().strip())
        return 0
    
    def _save_version(self, version: int) -> None:
        """保存新版本号"""
        version_file = self.cache_dir / "version"
        version_file.write_text(str(version))
    
    # 只读接口实现（在线服务使用）
    def query(self, table: str, symbols: Optional[List[str]] = None, 
              start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
              filters: Optional[Dict[str, any]] = None) -> pd.DataFrame:
        # 检查是否有新版本，自动增量加载
        latest_version = self._load_current_version()
        if latest_version > self.current_version:
            self.cache_manager.incremental_load(latest_version)
            self.current_version = latest_version
        return self.cache_manager.query(table, symbols, start_date, end_date, filters)
    
    def exists(self, table: str, symbols: Optional[List[str]] = None,
               start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
        return self.cache_manager.exists(table, symbols, start_date, end_date)
    
    def get_metadata(self, table: str) -> Dict[str, any]:
        return self.cache_manager.get_metadata(table)
    
    # 只写接口实现（离线任务使用）
    def write(self, table: str, data: pd.DataFrame, overwrite: bool = False) -> int:
        if table not in self.pending_writes:
            self.pending_writes[table] = []
        self.pending_writes[table].append(data)
        return len(data)
    
    def delete(self, table: str, symbols: Optional[List[str]] = None,
               start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        # 标记删除范围，commit时执行
        delete_marker = {
            "type": "delete",
            "table": table,
            "symbols": symbols,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
        marker_file = self.tmp_dir / f"delete_{table}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"
        marker_file.write_text(json.dumps(delete_marker))
        return 0
    
    def commit(self) -> None:
        """提交所有写入操作，原子性更新数据"""
        try:
            # 1. 写入所有临时数据
            for table, dfs in self.pending_writes.items():
                full_data = pd.concat(dfs, ignore_index=True)
                tmp_table_dir = self.tmp_dir / table
                tmp_table_dir.mkdir(exist_ok=True)
                self.cache_manager._write_parquet(full_data, tmp_table_dir)
            
            # 2. 执行删除操作
            for marker_file in self.tmp_dir.glob("delete_*.json"):
                delete_op = json.loads(marker_file.read_text())
                self.cache_manager.delete(
                    delete_op["table"],
                    delete_op["symbols"],
                    datetime.fromisoformat(delete_op["start_date"]) if delete_op["start_date"] else None,
                    datetime.fromisoformat(delete_op["end_date"]) if delete_op["end_date"] else None
                )
            
            # 3. 原子性移动临时文件到正式目录
            for table in self.pending_writes.keys():
                tmp_table_dir = self.tmp_dir / table
               正式_table_dir = self.cache_dir / table
                for file in tmp_table_dir.glob("*.parquet"):
                    shutil.move(str(file), str(正式_table_dir / file.name))
            
            # 4. 升级版本号
            new_version = self.current_version + 1
            self._save_version(new_version)
            
            # 5. 清理临时目录
            shutil.rmtree(self.tmp_dir)
            
        except Exception as e:
            self.rollback()
            raise WriteConflictError(f"Commit failed: {str(e)}") from e
    
    def rollback(self) -> None:
        """回滚所有未提交的写入"""
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.pending_writes.clear()
