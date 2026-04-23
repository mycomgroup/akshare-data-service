from __future__ import annotations

from pathlib import Path

import yaml


_ALLOWED_SEVERITY = {"error", "warning", "info", "critical", "high", "medium", "low"}


def _quality_files() -> list[Path]:
    return sorted(Path("config/quality").glob("*.yaml"))


def test_quality_rule_files_exist() -> None:
    files = _quality_files()
    assert files, "expected quality rule yaml files under config/quality"


def test_quality_rule_config_contains_rules() -> None:
    for file in _quality_files():
        payload = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
        rules = payload.get("rules", [])
        assert rules, f"{file} should define rules"
        for rule in rules:
            assert rule.get("rule_id"), f"{file} contains rule without rule_id"
            assert rule.get("type"), f"{file} contains rule without type"
            assert rule.get("severity") in _ALLOWED_SEVERITY, (
                f"{file} has unsupported severity"
            )
