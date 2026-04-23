"""Executor abstractions for ingestion workloads."""

from akshare_data.ingestion.executor.base import (
    ExecutionContext,
    ExecutionMode,
    ExecutionResult,
    Executor,
    ExecutorStats,
)

__all__ = [
    "ExecutionContext",
    "ExecutionMode",
    "ExecutionResult",
    "Executor",
    "ExecutorStats",
]
