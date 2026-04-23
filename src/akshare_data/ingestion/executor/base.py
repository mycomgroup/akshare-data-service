"""Unified executor contracts for ingestion and offline workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, Mapping, MutableMapping, Optional, TypeVar

TaskT = TypeVar("TaskT")
ResultT = TypeVar("ResultT")
PayloadT = TypeVar("PayloadT")


class ExecutionMode(str, Enum):
    """Execution mode."""

    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"


@dataclass(frozen=True)
class ExecutionContext:
    """Context for structured executor interface."""

    request_id: str
    batch_id: str
    source: str
    dataset: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutorContext:
    """Context for legacy task executors."""

    batch_id: str = ""
    run_id: str = ""
    trigger: str = "manual"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutorStats:
    """Execution metrics."""

    attempt: int = 1
    latency_ms: float = 0.0
    input_count: int = 0
    output_count: int = 0


@dataclass(frozen=True)
class ExecutionResult(Generic[PayloadT]):
    """Unified structured execution result."""

    ok: bool
    payload: Optional[PayloadT] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stats: ExecutorStats = field(default_factory=ExecutorStats)
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_name: str = ""
    rows: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def success(self) -> bool:
        return self.ok

    @property
    def error(self) -> str:
        return self.error_message or self.error_code or ""

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

    @classmethod
    def create_success(
        cls,
        payload: Optional[PayloadT] = None,
        *,
        stats: Optional[ExecutorStats] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_name: str = "",
        rows: int = 0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> "ExecutionResult[PayloadT]":
        start = started_at or datetime.now(timezone.utc)
        end = finished_at or datetime.now(timezone.utc)
        count = rows
        if count == 0 and payload is not None and hasattr(payload, "__len__"):
            try:
                count = int(len(payload))
            except TypeError:
                count = 0
        result_stats = stats or ExecutorStats(
            latency_ms=max(0.0, (end - start).total_seconds() * 1000),
            input_count=1,
            output_count=count,
        )
        return cls(
            ok=True,
            payload=payload,
            stats=result_stats,
            metadata=metadata or {},
            task_name=task_name,
            rows=count,
            started_at=start,
            finished_at=end,
        )

    @classmethod
    def create_failure(
        cls,
        *,
        error_code: str,
        error_message: str,
        stats: Optional[ExecutorStats] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_name: str = "",
        rows: int = 0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> "ExecutionResult[PayloadT]":
        start = started_at or datetime.now(timezone.utc)
        end = finished_at or datetime.now(timezone.utc)
        result_stats = stats or ExecutorStats(
            latency_ms=max(0.0, (end - start).total_seconds() * 1000),
            input_count=1,
            output_count=rows,
        )
        return cls(
            ok=False,
            error_code=error_code,
            error_message=error_message,
            stats=result_stats,
            metadata=metadata or {},
            task_name=task_name,
            rows=rows,
            started_at=start,
            finished_at=end,
        )

    # Backward-compatible constructors.
    success_result = create_success
    failure_result = create_failure


@dataclass(frozen=True)
class TaskExecutionResult(Generic[PayloadT]):
    """Legacy task execution result shape."""

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


class Executor(ABC, Generic[TaskT, ResultT]):
    """Structured executor abstraction."""

    mode: ExecutionMode = ExecutionMode.SYNC

    def __enter__(self) -> "Executor[TaskT, ResultT]":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        """Optional resource setup hook."""

    def close(self) -> None:
        """Optional resource cleanup hook."""

    @abstractmethod
    def execute(
        self,
        task: TaskT,
        context: ExecutionContext | None = None,
    ) -> ResultT:
        """Execute one task."""

    def healthcheck(self) -> bool:
        return True


class BaseTaskExecutor(ABC, Generic[TaskT, PayloadT]):
    """Task-style executor abstraction for offline workflows."""

    @abstractmethod
    def run(
        self,
        task: TaskT,
        *,
        context: Optional[ExecutorContext] = None,
    ) -> TaskExecutionResult[PayloadT]:
        """Run a task and return a normalized legacy result."""

    def healthcheck(self) -> bool:
        return True

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
    ) -> TaskExecutionResult[PayloadT]:
        """Helper to build normalized results with timestamps."""
        start = started_at or datetime.now(timezone.utc)
        end = finished_at or datetime.now(timezone.utc)
        return TaskExecutionResult(
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
    "BaseTaskExecutor",
    "ExecutionContext",
    "ExecutionMode",
    "ExecutionResult",
    "Executor",
    "ExecutorContext",
    "ExecutorStats",
    "TaskExecutionResult",
]
