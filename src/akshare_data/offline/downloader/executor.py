"""下载任务执行器"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from akshare_data.ingestion.executor.base import (
    BaseTaskExecutor,
    ExecutionResult,
    ExecutorContext,
)
from akshare_data.offline.core.errors import DownloadError
from akshare_data.offline.core.retry import RetryConfig, retry
from akshare_data.offline.downloader.rate_limiter import DomainRateLimiter
from akshare_data.offline.downloader.task_builder import DownloadTask
from akshare_data.offline.field_mapper import EXTENDED_CN_TO_EN

logger = logging.getLogger("akshare_data")

_RETRY_CONFIG = RetryConfig(max_retries=2, delay=1.0, backoff=1.0)


class TaskExecutor(BaseTaskExecutor[DownloadTask, pd.DataFrame]):
    """下载任务执行器.

    兼容旧接口 ``execute(task) -> dict``，同时实现统一执行器接口
    ``run(task, context) -> ExecutionResult``。
    """

    def __init__(self, rate_limiter: DomainRateLimiter, cache_manager=None):
        self._rate_limiter = rate_limiter
        self._cache_manager = cache_manager

    def run(
        self,
        task: DownloadTask,
        *,
        context: Optional[ExecutorContext] = None,
    ) -> ExecutionResult[pd.DataFrame]:
        """执行单个下载任务，返回统一结果对象。"""
        started_at = datetime.now(timezone.utc)
        metadata = {
            "interface": task.interface,
            "table": task.table,
            "rate_limit_key": task.rate_limit_key,
        }
        if context:
            metadata["batch_id"] = context.batch_id
            metadata["run_id"] = context.run_id
            metadata["trigger"] = context.trigger

        try:
            self._rate_limiter.wait(task.rate_limit_key)
            df = self._call_akshare(task.func, **task.kwargs)
        except Exception as e:
            logger.error("Task %s failed: %s", task.interface, e)
            return self.result(
                success=False,
                task_name=task.interface,
                error=str(e),
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                metadata=metadata,
            )

        if df is None or df.empty:
            return self.result(
                success=False,
                task_name=task.interface,
                error="Empty data",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                metadata=metadata,
            )

        if self._cache_manager:
            self._write_to_cache(task, df)

        return self.result(
            success=True,
            task_name=task.interface,
            rows=len(df),
            payload=df,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            metadata=metadata,
        )

    def execute(self, task: DownloadTask) -> Dict[str, Any]:
        """兼容旧调用方：返回 dict 结构。"""
        return self.run(task).to_dict()

    @retry(_RETRY_CONFIG)
    def _call_akshare(self, func_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """调用 AkShare 函数"""
        import akshare as ak

        func = getattr(ak, func_name, None)
        if func is None:
            raise DownloadError(f"Function {func_name} not found")
        return func(**kwargs)

    def _write_to_cache(self, task: DownloadTask, df: pd.DataFrame):
        """写入缓存（先做字段规范化）"""
        if self._cache_manager:
            try:
                df = self._normalize_columns(task, df)
                self._cache_manager.write(
                    table=task.table,
                    data=df,
                    storage_layer="duckdb",
                    partition_by="date",
                )
            except Exception as e:
                logger.warning("Failed to write cache for %s: %s", task.table, e)

    @staticmethod
    def _normalize_columns(task: DownloadTask, df: pd.DataFrame) -> pd.DataFrame:
        """按任务映射或全局映射重命名列"""
        mapping = task.output_mapping if task.output_mapping else EXTENDED_CN_TO_EN
        rename_map = {col: mapping[col] for col in df.columns if col in mapping}
        if rename_map:
            df = df.rename(columns=rename_map)
        return df
