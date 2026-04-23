"""Unified extraction executor contracts.

Task executors in online ingestion, offline downloader, and backfill/replay
should all conform to this contract so scheduling, audit and metrics can be
shared.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generic, Mapping, MutableMapping, Optional, TypeVar


TaskT = TypeVar("TaskT")
PayloadT = TypeVar("PayloadT")


@dataclass(frozen=True)
class ExecutorContext:
    """Execution context shared by all task runs."""

    batch_id: str = ""
    run_id: str = ""
    trigger: str = "manual"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult(Generic[PayloadT]):
    """Unified result model for extraction execution."""

    success: bool
    task_name: str
    rows: int = 0
    payload: Optional[PayloadT] = None
    error: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return int((self.finished_at - self.started_at).total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task": self.task_name,
            "rows": self.rows,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "metadata": dict(self.metadata),
        }


class BaseTaskExecutor(ABC, Generic[TaskT, PayloadT]):
    """Base contract for all extract task executors."""

    @abstractmethod
    def run(
        self,
        task: TaskT,
        *,
        context: Optional[ExecutorContext] = None,
    ) -> ExecutionResult[PayloadT]:
        """Run a task and return unified execution result."""

    def result(
        self,
        *,
        success: bool,
        task_name: str,
        rows: int = 0,
        payload: Optional[PayloadT] = None,
        error: str = "",
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[MutableMapping[str, Any]] = None,
    ) -> ExecutionResult[PayloadT]:
        """Helper to build normalized results with timestamps."""
        start = started_at or datetime.now(timezone.utc)
        end = finished_at or datetime.now(timezone.utc)
        return ExecutionResult(
            success=success,
            task_name=task_name,
            rows=rows,
            payload=payload,
            error=error,
            started_at=start,
            finished_at=end,
            metadata=dict(metadata or {}),
        )


__all__ = [
    "ExecutorContext",
    "ExecutionResult",
    "BaseTaskExecutor",
]
