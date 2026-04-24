#!/usr/bin/env python3
"""重新生成 akshare_registry.yaml - 包含输出字段捕获"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from akshare_data.offline.registry.builder import RegistryBuilder
from akshare_data.offline.registry.exporter import RegistryExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("regenerate_registry")


def parse_args():
    parser = argparse.ArgumentParser(description="重新生成 akshare_registry.yaml")
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="代理地址，格式: http://host:port 或 socks5://host:port",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径",
    )
    return parser.parse_args()


def setup_proxy(proxy_url: str):
    """设置代理环境变量"""
    if not proxy_url:
        return
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url
    logger.info(f"Proxy set to: {proxy_url}")


def main():
    args = parse_args()

    if args.proxy:
        setup_proxy(args.proxy)

    project_root = Path(__file__).parent.parent
    output_file = Path(args.output) if args.output else project_root / "akshare_registry.yaml"

    logger.info("Starting registry regeneration with output field capture...")
    logger.info(f"Output file: {output_file}")

    start_time = time.time()

    try:
        builder = RegistryBuilder()
        logger.info("Scanning AkShare functions...")
        registry = builder.build()
    except Exception as e:
        logger.error(f"Failed to build registry: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    interface_count = len(registry.get("interfaces", {}))
    interfaces_with_output = sum(
        1 for iface in registry["interfaces"].values()
        if iface.get("output_fields")
    )

    logger.info(f"Scanned {interface_count} interfaces in {elapsed:.1f}s")
    logger.info(f"Interfaces with output fields: {interfaces_with_output}")

    try:
        exporter = RegistryExporter()
        result_path = exporter.export_yaml(registry, output_file)
    except Exception as e:
        logger.error(f"Failed to export registry: {e}")
        sys.exit(1)

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
    print(f"  - Success: {stats.get('success', 0)}")
    print(f"  - Timeout: {stats.get('timeout', 0)}")
    print(f"  - Non-DataFrame: {stats.get('non_df', 0)}")
    print(f"  - Failed: {stats.get('failed', 0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()