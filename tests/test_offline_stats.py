"""tests/test_offline_stats.py

调用统计分析器测试 (CallStatsAnalyzer)
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from akshare_data.offline.analyzer.access_log.stats import CallStatsAnalyzer

pytestmark = pytest.mark.unit


class TestCallStatsAnalyzerTimezone:
    """测试时区处理"""

    def test_read_logs_with_aware_timestamps(self):
        """测试读取带时区的时间戳"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                }
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result

    def test_read_logs_with_naive_timestamps(self):
        """测试读取不带时区的时间戳"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now()
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                }
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result

    def test_future_timestamp_does_not_inflate_recency(self):
        """测试未来时间戳不会导致 recency 分数失真"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            future_ts = (now + timedelta(days=30)).isoformat()
            entries = [
                {
                    "ts": future_ts,
                    "interface": "future_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
                {
                    "ts": now.isoformat(),
                    "interface": "normal_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)

            future_score = result["priorities"]["future_api"]["score"]
            normal_score = result["priorities"]["normal_api"]["score"]
            assert future_score <= normal_score or future_score <= 100

    def test_mixed_timezone_timestamps(self):
        """测试混合时区时间戳"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now_utc = datetime.now(timezone.utc)
            now_naive = datetime.now()
            entries = [
                {
                    "ts": now_utc.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
                {
                    "ts": now_naive.isoformat(),
                    "interface": "test_api",
                    "symbol": "000002",
                    "cache_hit": True,
                    "latency_ms": 50,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result


class TestCallStatsAnalyzerAggregation:
    """测试聚合逻辑"""

    def test_aggregate_basic(self):
        """测试基本聚合"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": True,
                    "latency_ms": 50,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)

            api_data = result["priorities"]["test_api"]
            assert api_data["call_count_7d"] == 2
            assert api_data["miss_rate_7d"] == 0.5

    def test_aggregate_latency_string_value(self):
        """测试 latency_ms 为字符串类型时不崩溃"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": "100",
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result

    def test_aggregate_invalid_timestamp_skipped(self):
        """测试无效时间戳被跳过"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": "invalid-timestamp",
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result


class TestCallStatsAnalyzerScoring:
    """测试评分算法"""

    def test_score_normalization(self):
        """测试分数归一化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = []
            for i in range(100):
                entries.append(
                    {
                        "ts": now.isoformat(),
                        "interface": "hot_api",
                        "symbol": "000001",
                        "cache_hit": False,
                        "latency_ms": 100,
                    }
                )
            for i in range(10):
                entries.append(
                    {
                        "ts": now.isoformat(),
                        "interface": "cold_api",
                        "symbol": "000001",
                        "cache_hit": True,
                        "latency_ms": 50,
                    }
                )
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)

            hot_score = result["priorities"]["hot_api"]["score"]
            cold_score = result["priorities"]["cold_api"]["score"]
            assert hot_score > cold_score

    def test_empty_aggregation(self):
        """测试空聚合"""
        analyzer = CallStatsAnalyzer()
        scored = analyzer._score({})
        assert scored == {}

    def test_max_calls_zero(self):
        """测试 max_calls 为 0 时不崩溃"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert "priorities" in result


class TestCallStatsAnalyzerConfig:
    """测试配置生成"""

    def test_config_structure(self):
        """测试配置结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            output_path = Path(tmpdir) / "priority.yaml"
            analyzer = CallStatsAnalyzer(log_dir=tmpdir, output_path=str(output_path))
            config = analyzer.analyze(window_days=7)

            assert "generated_at" in config
            assert "window" in config
            assert "priorities" in config
            assert "global" in config
            assert "total_calls_7d" in config["global"]
            assert "overall_miss_rate" in config["global"]

    def test_config_saved_as_yaml(self):
        """测试配置保存为 YAML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            entries = [
                {
                    "ts": now.isoformat(),
                    "interface": "test_api",
                    "symbol": "000001",
                    "cache_hit": False,
                    "latency_ms": 100,
                },
            ]
            with open(log_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            output_path = Path(tmpdir) / "priority.yaml"
            analyzer = CallStatsAnalyzer(log_dir=tmpdir, output_path=str(output_path))
            analyzer.analyze(window_days=7)

            assert output_path.exists()
            with open(output_path) as f:
                config = yaml.safe_load(f)
            assert "priorities" in config

    def test_recommend_strategy(self):
        """测试策略推荐"""
        analyzer = CallStatsAnalyzer()

        high_miss = analyzer._recommend_strategy(
            {
                "miss_rate": 0.6,
                "call_count": 100,
                "score": 80,
            }
        )
        assert high_miss["mode"] == "incremental"
        assert high_miss["frequency"] == "hourly"

        medium_miss = analyzer._recommend_strategy(
            {
                "miss_rate": 0.4,
                "call_count": 10,
                "score": 70,
            }
        )
        assert medium_miss["mode"] == "incremental"
        assert medium_miss["frequency"] == "daily"

        low_score = analyzer._recommend_strategy(
            {
                "miss_rate": 0.1,
                "call_count": 5,
                "score": 40,
            }
        )
        assert low_score["mode"] == "full"
        assert low_score["frequency"] == "weekly"

        very_low = analyzer._recommend_strategy(
            {
                "miss_rate": 0.05,
                "call_count": 1,
                "score": 10,
            }
        )
        assert very_low["mode"] == "full"
        assert very_low["frequency"] == "monthly"


class TestCallStatsAnalyzerEdgeCases:
    """测试边界条件"""

    def test_no_log_files(self):
        """测试没有日志文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            result = analyzer.analyze(window_days=7)
            assert result == {}

    def test_log_file_with_invalid_json(self):
        """测试日志文件包含无效 JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log"
            now = datetime.now(timezone.utc)
            with open(log_file, "w") as f:
                f.write("invalid json\n")
                f.write(
                    json.dumps(
                        {
                            "ts": now.isoformat(),
                            "interface": "test",
                            "symbol": "001",
                            "cache_hit": False,
                            "latency_ms": 100,
                        }
                    )
                    + "\n"
                )

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            entries = analyzer._read_logs(window_days=7)
            assert len(entries) == 1

    def test_rotated_log_file_parsing(self):
        """测试轮转日志文件解析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            now = datetime.now(timezone.utc)
            recent_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            old_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

            recent_file = Path(tmpdir) / f"access.log.{recent_date}"
            old_file = Path(tmpdir) / f"access.log.{old_date}"

            entry = {
                "ts": now.isoformat(),
                "interface": "test_api",
                "symbol": "000001",
                "cache_hit": False,
                "latency_ms": 100,
            }

            with open(recent_file, "w") as f:
                f.write(json.dumps(entry) + "\n")
            with open(old_file, "w") as f:
                f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            entries = analyzer._read_logs(window_days=7)
            assert len(entries) == 1

    def test_rotated_log_file_invalid_date_format(self):
        """测试轮转日志文件名日期格式无效"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "access.log.invalid"
            now = datetime.now(timezone.utc)
            entry = {
                "ts": now.isoformat(),
                "interface": "test_api",
                "symbol": "000001",
                "cache_hit": False,
                "latency_ms": 100,
            }
            with open(log_file, "w") as f:
                f.write(json.dumps(entry) + "\n")

            analyzer = CallStatsAnalyzer(log_dir=tmpdir)
            entries = analyzer._read_logs(window_days=7)
            assert len(entries) == 1
