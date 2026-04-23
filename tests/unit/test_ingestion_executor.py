from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from akshare_data.ingestion.executor.base import BaseTaskExecutor, ExecutorContext
from akshare_data.offline.downloader.executor import TaskExecutor
from akshare_data.offline.downloader.task_builder import DownloadTask


class _DummyExecutor(BaseTaskExecutor[str, int]):
    def run(self, task: str, *, context: ExecutorContext | None = None):
        start = datetime.now(timezone.utc)
        return self.result(
            success=True,
            task_name=task,
            payload=1,
            rows=1,
            started_at=start,
            finished_at=datetime.now(timezone.utc),
            metadata={"trigger": context.trigger if context else "manual"},
        )


def test_base_executor_result_to_dict_contains_duration() -> None:
    exe = _DummyExecutor()
    res = exe.run("demo", context=ExecutorContext(trigger="scheduler"))

    payload = res.to_dict()
    assert payload["success"] is True
    assert payload["task"] == "demo"
    assert payload["rows"] == 1
    assert payload["duration_ms"] >= 0
    assert payload["metadata"]["trigger"] == "scheduler"


def test_offline_task_executor_run_success(monkeypatch) -> None:
    class _RateLimiter:
        def wait(self, key: str) -> None:
            return None

    class _CacheManager:
        def write(self, **kwargs) -> None:
            self.last = kwargs

    task = DownloadTask(
        interface="stock_zh_a_hist",
        func="stock_zh_a_hist",
        table="stock_daily",
        kwargs={"symbol": "000001"},
    )

    exe = TaskExecutor(rate_limiter=_RateLimiter(), cache_manager=_CacheManager())

    monkeypatch.setattr(
        exe,
        "_call_akshare",
        lambda *args, **kwargs: pd.DataFrame([{"开盘": 10.0, "收盘": 10.5}]),
    )

    result = exe.run(task, context=ExecutorContext(batch_id="b1", run_id="r1"))
    assert result.success is True
    assert result.rows == 1
    assert result.metadata["batch_id"] == "b1"

    legacy = exe.execute(task)
    assert legacy["success"] is True
    assert legacy["task"] == "stock_zh_a_hist"


def test_offline_task_executor_run_empty_data(monkeypatch) -> None:
    class _RateLimiter:
        def wait(self, key: str) -> None:
            return None

    task = DownloadTask(
        interface="stock_zh_a_hist",
        func="stock_zh_a_hist",
        table="stock_daily",
        kwargs={"symbol": "000001"},
    )
    exe = TaskExecutor(rate_limiter=_RateLimiter())

    monkeypatch.setattr(exe, "_call_akshare", lambda *args, **kwargs: pd.DataFrame())

    result = exe.run(task)
    assert result.success is False
    assert result.error == "Empty data"
