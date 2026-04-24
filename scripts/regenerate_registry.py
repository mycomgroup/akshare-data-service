#!/usr/bin/env python3
"""重新生成 akshare_registry.yaml - 包含输出字段捕获"""

from __future__ import annotations

import logging
import sys
import time
import warnings
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akshare_data.offline.registry.builder import RegistryBuilder
from akshare_data.offline.registry.exporter import RegistryExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("regenerate_registry")


class OutputCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        msg = self.format(record)
        self.messages.append(msg)


def main():
    project_root = Path(__file__).parent.parent
    output_file = project_root / "config" / "akshare_registry.yaml"

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()

    old_warnings_filters = warnings.filters[:]
    warnings.filterwarnings("ignore")

    try:
        logger.info("Starting registry regeneration with output field capture...")
        logger.info(f"Output file: {output_file}")

        start_time = time.time()

        builder = RegistryBuilder()
        logger.info("Scanning AkShare functions...")
        registry = builder.build()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        warnings.filters[:] = old_warnings_filters

    elapsed = time.time() - start_time
    interface_count = len(registry.get("interfaces", {}))
    interfaces_with_output = sum(
        1 for iface in registry["interfaces"].values()
        if iface.get("output_fields")
    )

    logger.info(f"Scanned {interface_count} interfaces in {elapsed:.1f}s")
    logger.info(f"Interfaces with output fields: {interfaces_with_output}")

    exporter = RegistryExporter()
    result_path = exporter.export_yaml(registry, output_file)

    total_elapsed = time.time() - start_time
    logger.info(f"Registry exported to {result_path}")
    logger.info(f"Total time: {total_elapsed:.1f}s")

    stats = builder.output_capture.get_stats()
    print(f"\n{'='*60}")
    print(f"Registry regeneration complete!")
    print(f"  Total interfaces: {interface_count}")
    print(f"  With output fields: {interfaces_with_output}")
    print(f"  Output file: {output_file}")
    print(f"  Total time: {total_elapsed:.1f}s")
    print(f"\nCapture stats:")
    print(f"  - Code parse: {interfaces_with_output - stats.get('success', 0)}")
    print(f"  - Runtime success: {stats.get('success', 0)}")
    print(f"  - Timeout: {stats.get('timeout', 0)}")
    print(f"  - Non-DataFrame: {stats.get('non_df', 0)}")
    print(f"  - Failed: {stats.get('failed', 0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()