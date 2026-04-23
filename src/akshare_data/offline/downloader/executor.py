"""下载任务执行器。"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from akshare_data.ingestion.executor.base import (
    ExecutionContext,
    ExecutionMode,
    ExecutionResult as UnifiedExecutionResult,
    Executor,
    ExecutorStats,
)
from akshare_data.offline.core.errors import DownloadError
from akshare_data.offline.core.retry import RetryConfig, retry
from akshare_data.offline.downloader.rate_limiter import DomainRateLimiter
from akshare_data.offline.downloader.task_builder import DownloadTask
from akshare_data.offline.field_mapper import EXTENDED_CN_TO_EN

logger = logging.getLogger("akshare_data")

_RETRY_CONFIG = RetryConfig(max_retries=2, delay=1.0, backoff=1.0)


class TaskExecutor(Executor[DownloadTask, pd.DataFrame]):
    """下载任务执行器。"""

    mode = ExecutionMode.SYNC

    def __init__(self, rate_limiter: DomainRateLimiter, cache_manager=None):
        self._rate_limiter = rate_limiter
        self._cache_manager = cache_manager

    def execute(self, task: DownloadTask, context: ExecutionContext | None = None) -> Dict[str, Any]:
        """执行单个下载任务（兼容旧接口）。"""
        if context is None:
            context = ExecutionContext(
                request_id=f"download-{task.interface}",
                batch_id=f"batch-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                source="akshare",
                dataset=task.table,
            )

        result = self.execute_structured(task, context=context)
        if not result.ok:
            return {
                "success": False,
                "error": result.error_message or result.error_code,
                "task": task.interface,
            }

        payload = result.payload if result.payload is not None else pd.DataFrame()
        return {
            "success": True,
            "rows": len(payload),
            "task": task.interface,
        }

    def execute_structured(
        self,
        task: DownloadTask,
        *,
        context: ExecutionContext,
    ) -> UnifiedExecutionResult[pd.DataFrame]:
        """执行单个下载任务并返回统一结构结果。"""
        start = time.perf_counter()

        try:
            self._rate_limiter.wait(task.rate_limit_key)
            df = self._call_akshare(task.func, **task.kwargs)
        except Exception as e:
            logger.error("Task %s failed: %s", task.interface, e)
            return UnifiedExecutionResult.failure(
                error_code="download_failed",
                error_message=str(e),
                stats=ExecutorStats(latency_ms=(time.perf_counter() - start) * 1000),
                metadata={
                    "task": task.interface,
                    "request_id": context.request_id,
                    "batch_id": context.batch_id,
                },
            )

        if df is None or df.empty:
            return UnifiedExecutionResult.failure(
                error_code="empty_data",
                error_message="Empty data",
                stats=ExecutorStats(latency_ms=(time.perf_counter() - start) * 1000),
                metadata={
                    "task": task.interface,
                    "request_id": context.request_id,
                    "batch_id": context.batch_id,
                },
            )

        if self._cache_manager:
            self._write_to_cache(task, df)

        return UnifiedExecutionResult.success(
            payload=df,
            stats=ExecutorStats(
                latency_ms=(time.perf_counter() - start) * 1000,
                input_count=1,
                output_count=len(df),
            ),
            metadata={
                "task": task.interface,
                "request_id": context.request_id,
                "batch_id": context.batch_id,
            },
        )

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
