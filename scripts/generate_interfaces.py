#!/usr/bin/env python3
"""从 akshare_registry.yaml 生成 config/interfaces/*.yaml"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml

from akshare_data.offline.generator import InterfaceSkeletonGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("generate_interfaces")


def main():
    project_root = Path(__file__).parent.parent
    registry_file = project_root / "akshare_registry.yaml"
    output_dir = project_root / "config" / "interfaces" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading registry from {registry_file}...")
    with open(registry_file, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    total_interfaces = len(registry.get("interfaces", {}))
    logger.info(f"Loaded {total_interfaces} interfaces from registry")

    start_time = time.time()

    generator = InterfaceSkeletonGenerator()
    output_files = generator.generate_all(
        registry,
        output_dir,
        categories=None,
    )

    elapsed = time.time() - start_time

    total_generated = sum(len(yaml.safe_load(open(f))) for f in output_files.values())

    logger.info(f"Generated {len(output_files)} category files in {elapsed:.1f}s")

    print(f"\n{'='*60}")
    print("Interface generation complete!")
    print(f"  Total interfaces: {total_interfaces}")
    print(f"  Output directory: {output_dir}")
    print(f"  Total time: {elapsed:.1f}s")
    print("\nGenerated files:")
    for cat, path in output_files.items():
        count = len(yaml.safe_load(open(path, encoding="utf-8")))
        print(f"  {cat}: {count} interfaces -> {path.name}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()