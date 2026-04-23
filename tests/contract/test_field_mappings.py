from __future__ import annotations

from pathlib import Path

import yaml


def _mapping_files() -> list[Path]:
    base = Path("config/mappings/sources")
    return sorted(base.glob("*/*.yaml"))


def test_mapping_files_exist() -> None:
    files = _mapping_files()
    assert files, "expected mapping config files under config/mappings/sources"


def test_mapping_has_dataset_source_and_fields() -> None:
    for file in _mapping_files():
        payload = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
        assert payload.get("dataset"), f"{file} should include dataset"
        assert payload.get("source"), f"{file} should include source"

        fields = payload.get("fields", {})
        sub_sources = payload.get("sub_sources", {})
        assert fields or sub_sources, f"{file} should define fields or sub_sources"

        for src_field, spec in fields.items():
            assert src_field
            assert isinstance(spec, dict)
            assert spec.get("status") in {"active", "deprecated", "pending"}
            if spec.get("status") == "active":
                assert spec.get("standard_field"), (
                    f"{file} active field '{src_field}' missing standard_field"
                )
