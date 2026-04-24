"""tests/test_offline_report_modules.py

新架构报告模块测试 (HealthReportGenerator, QualityReportGenerator, ReportRenderer)
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from akshare_data.offline.report.health_report import HealthReportGenerator
from akshare_data.offline.report.quality_report import QualityReportGenerator
from akshare_data.offline.report.renderer import ReportRenderer

pytestmark = pytest.mark.unit


class TestReportRenderer:
    """测试 ReportRenderer"""

    def test_to_md_empty_dataframe(self):
        """测试空 DataFrame"""
        renderer = ReportRenderer()
        result = renderer.to_md(pd.DataFrame())
        assert result == ""

    def test_to_md_basic(self):
        """测试基本转换"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"name": ["foo", "bar"], "value": [1, 2]})
        result = renderer.to_md(df)
        assert "|name|value|" in result
        assert "|foo|1|" in result

    def test_to_md_exec_time_formatting(self):
        """测试 exec_time 列格式化"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"func_name": ["test"], "exec_time": [1.234]})
        result = renderer.to_md(df)
        assert "1.23s" in result

    def test_to_md_exec_time_string_value(self):
        """测试 exec_time 为非数值类型时不崩溃"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"func_name": ["test"], "exec_time": ["invalid"]})
        result = renderer.to_md(df)
        assert "invalid" in result

    def test_to_md_last_check_timestamp(self):
        """测试 last_check 时间戳格式化"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"name": ["test"], "last_check": [1704067200.0]})
        result = renderer.to_md(df)
        assert "01-01" in result

    def test_to_md_last_check_invalid_value(self):
        """测试 last_check 为无效值时不崩溃"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"name": ["test"], "last_check": ["invalid"]})
        result = renderer.to_md(df)
        assert "invalid" in result

    def test_render_markdown_sections(self):
        """测试 Markdown 报告渲染"""
        renderer = ReportRenderer()
        sections = {
            "Test Report": {
                "Total": 100,
                "Rate": "50.0%",
            }
        }
        result = renderer.render_markdown(sections)
        assert "# Test Report" in result
        assert "**Total**: 100" in result
        assert "**Rate**: 50.0%" in result

    def test_render_markdown_dataframe_content(self):
        """测试 DataFrame 内容渲染"""
        renderer = ReportRenderer()
        df = pd.DataFrame({"name": ["foo"], "value": [1]})
        sections = {"Data": df}
        result = renderer.render_markdown(sections)
        assert "# Data" in result
        assert "|name|value|" in result

    def test_render_markdown_list_content(self):
        """测试列表内容渲染"""
        renderer = ReportRenderer()
        sections = {"Items": ["item1", "item2"]}
        result = renderer.render_markdown(sections)
        assert "- item1" in result
        assert "- item2" in result

    def test_render_json(self):
        """测试 JSON 渲染"""
        renderer = ReportRenderer()
        data = {"key": "value", "nested": {"a": 1}}
        result = renderer.render_json(data)
        assert '"key": "value"' in result
        assert '"a": 1' in result

    def test_save_creates_parent_dirs(self):
        """测试保存时创建父目录"""
        renderer = ReportRenderer()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "report.md"
            renderer.save("# Test", output_path)
            assert output_path.exists()


class TestHealthReportGenerator:
    """测试 HealthReportGenerator"""

    def test_generate_empty_results(self):
        """测试空结果"""
        generator = HealthReportGenerator()
        result = generator.generate({})
        assert result == ""

    def test_generate_dict_results(self):
        """测试字典格式结果"""
        generator = HealthReportGenerator()
        results = {
            "func1": {"status": "Success", "exec_time": 1.0, "func_name": "func1"},
            "func2": {"status": "Failed", "exec_time": 2.0, "func_name": "func2"},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Health Audit Report" in result
                assert "Total APIs" in result

    def test_generate_list_results(self):
        """测试列表格式结果"""
        generator = HealthReportGenerator()
        results = [
            {"status": "Success", "exec_time": 1.0, "func_name": "func1"},
            {"status": "Failed", "exec_time": 2.0, "func_name": "func2"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Total APIs" in result

    def test_success_rate_exact_match(self):
        """测试成功率使用精确匹配，PartiallySuccess 不计入成功"""
        generator = HealthReportGenerator()
        results = [
            {"status": "Success", "exec_time": 1.0, "func_name": "func1"},
            {"status": "PartiallySuccess", "exec_time": 2.0, "func_name": "func2"},
            {"status": "SuccessWithWarning", "exec_time": 3.0, "func_name": "func3"},
            {"status": "Failed", "exec_time": 4.0, "func_name": "func4"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Available APIs" in result
                assert "25.0%" in result

    def test_status_column_non_string_values(self):
        """测试 status 列包含非字符串值时不崩溃"""
        generator = HealthReportGenerator()
        results = [
            {"status": "Success", "exec_time": 1.0, "func_name": "func1"},
            {"status": None, "exec_time": 2.0, "func_name": "func2"},
            {"status": 123, "exec_time": 3.0, "func_name": "func3"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Total APIs" in result

    def test_missing_status_column(self):
        """测试缺少 status 列时不崩溃"""
        generator = HealthReportGenerator()
        results = [
            {"exec_time": 1.0, "func_name": "func1"},
            {"exec_time": 2.0, "func_name": "func2"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Total APIs" in result

    def test_slowest_apis_all_columns_exist(self):
        """测试所有列存在时慢速 API 表格正确"""
        generator = HealthReportGenerator()
        results = [
            {"func_name": "slow", "exec_time": 10.0, "status": "Success"},
            {"func_name": "fast", "exec_time": 1.0, "status": "Success"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "slow" in result

    def test_slowest_apis_missing_columns(self):
        """测试缺少 func_name/status 列时不崩溃"""
        generator = HealthReportGenerator()
        results = [
            {"exec_time": 10.0},
            {"exec_time": 1.0},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(results)
                assert "Top 20 Slowest APIs" in result
                assert "exec_time" in result

    def test_output_filename_with_timestamp(self):
        """测试输出文件名包含时间戳"""
        generator = HealthReportGenerator()
        results = [{"status": "Success", "exec_time": 1.0, "func_name": "func1"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with patch.object(generator, "_output_dir", output_dir):
                generator.generate(results)
                files = list(output_dir.glob("health_report_*.md"))
                assert len(files) == 1
                assert "_" in files[0].name

    def test_custom_output_file(self):
        """测试自定义输出文件路径"""
        generator = HealthReportGenerator()
        results = [{"status": "Success", "exec_time": 1.0, "func_name": "func1"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "custom_report.md"
            generator.generate(results, output_file=output_file)
            assert output_file.exists()


class TestQualityReportGenerator:
    """测试 QualityReportGenerator"""

    def test_generate_none_input(self):
        """测试 None 输入"""
        generator = QualityReportGenerator()
        result = generator.generate(None)
        assert result == ""

    def test_generate_empty_dict_input(self):
        """测试空字典输入"""
        generator = QualityReportGenerator()
        result = generator.generate({})
        assert result == ""

    def test_generate_non_dict_input(self):
        """测试非字典输入"""
        generator = QualityReportGenerator()
        result = generator.generate([])
        assert result == ""

    def test_generate_basic(self):
        """测试基本质量报告生成"""
        generator = QualityReportGenerator()
        quality_results = {
            "table": "stock_daily",
            "symbol": "000001",
            "checks": {
                "completeness": {"completeness_ratio": 0.95, "is_complete": True},
            },
            "summary": {"overall_score": 95.0},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(quality_results)
                assert "Data Quality Report" in result
                assert "stock_daily" in result

    def test_generate_with_anomalies_dict(self):
        """测试包含异常检测结果"""
        generator = QualityReportGenerator()
        quality_results = {
            "table": "stock_daily",
            "checks": {
                "anomalies": {
                    "anomaly_count": 2,
                    "anomalies": [
                        {"type": "price", "value": 25.0},
                        {"type": "volume", "value": 1000},
                    ],
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(quality_results)
                assert "Total Anomalies" in result
                assert "2" in result

    def test_generate_with_anomalies_non_dict(self):
        """测试异常检测结果为非字典时不崩溃"""
        generator = QualityReportGenerator()
        quality_results = {
            "table": "stock_daily",
            "checks": {
                "anomalies": "invalid_data",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(quality_results)
                assert "Data Quality Report" in result

    def test_generate_with_empty_anomalies_list(self):
        """测试异常列表为空"""
        generator = QualityReportGenerator()
        quality_results = {
            "table": "stock_daily",
            "checks": {
                "anomalies": {
                    "anomaly_count": 0,
                    "anomalies": [],
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generator, "_output_dir", Path(tmpdir)):
                result = generator.generate(quality_results)
                assert "Total Anomalies" in result

    def test_output_filename_with_timestamp(self):
        """测试输出文件名包含时间戳"""
        generator = QualityReportGenerator()
        quality_results = {"table": "stock_daily"}
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with patch.object(generator, "_output_dir", output_dir):
                generator.generate(quality_results)
                files = list(output_dir.glob("quality_report_*.md"))
                assert len(files) == 1
                assert "_" in files[0].name

    def test_custom_output_file(self):
        """测试自定义输出文件路径"""
        generator = QualityReportGenerator()
        quality_results = {"table": "stock_daily"}
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "custom_quality.md"
            generator.generate(quality_results, output_file=output_file)
            assert output_file.exists()
