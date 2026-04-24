"""快速升级脚本 - 一键升级手动配置"""

import argparse
import json
import logging
from pathlib import Path
import yaml
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scanner_v2 import EnhancedScanner
from runtime_prober import RuntimeProber
from semantic_inferrer import SemanticInferrer
from config_merger import ConfigMerger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("upgrade_config")


def upgrade_config(
    manual_config_dir: Path,
    output_dir: Path,
    probe_limit: int = 100,
):
    """升级手动配置"""
    
    # 1. 增强扫描
    logger.info("=== Step 1: Enhanced Scanning ===")
    scanner = EnhancedScanner()
    scanned = scanner.scan_all()
    
    scanned_file = output_dir / "scanned_enhanced.yaml"
    with open(scanned_file, "w") as f:
        yaml.dump(scanned, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Scanned {len(scanned)} functions -> {scanned_file}")
    
    # 2. 运行时探测
    logger.info("=== Step 2: Runtime Probing ===")
    prober = RuntimeProber(max_workers=5, rate_limit=1.0)
    
    # 提取需要探测的函数名
    func_names_to_probe = extract_func_names_from_manual_config(manual_config_dir)
    func_names_to_probe = func_names_to_probe[:probe_limit]  # 限制数量
    
    probed = prober.probe_batch(func_names_to_probe)
    
    probed_file = output_dir / "probed_schemas.yaml"
    with open(probed_file, "w") as f:
        yaml.dump(probed, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Probed {len(probed)} functions -> {probed_file}")
    
    # 3. 生成高质量骨架
    logger.info("=== Step 3: Generate Skeletons ===")
    inferrer = SemanticInferrer()
    
    generated_config = {}
    for func_name, probed_schema in probed.items():
        func_info = scanned.get(func_name, {})
        
        skeleton = generate_skeleton_from_probed(
            func_name,
            func_info,
            probed_schema,
            inferrer,
        )
        
        category = infer_category(func_name)
        if category not in generated_config:
            generated_config[category] = {}
        generated_config[category][func_name] = skeleton
    
    generated_file = output_dir / "generated_enhanced.yaml"
    with open(generated_file, "w") as f:
        yaml.dump(generated_config, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Generated skeletons -> {generated_file}")
    
    # 4. 升级手动配置
    logger.info("=== Step 4: Upgrade Manual Config ===")
    merger = ConfigMerger()
    
    manual_config = load_manual_config(manual_config_dir)
    upgraded_config, changes = merger.upgrade_manual_config(
        manual_config,
        generated_config,
    )
    
    upgraded_file = output_dir / "upgraded_config.yaml"
    with open(upgraded_file, "w") as f:
        yaml.dump(upgraded_config, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Upgraded config -> {upgraded_file}")
    
    # 5. 生成报告
    logger.info("=== Step 5: Generate Report ===")
    report_file = output_dir / "upgrade_report.md"
    merger.generate_report(changes, report_file)
    logger.info(f"Report -> {report_file}")
    
    return {
        "scanned": scanned_file,
        "probed": probed_file,
        "generated": generated_file,
        "upgraded": upgraded_file,
        "report": report_file,
    }


def extract_func_names_from_manual_config(config_dir: Path) -> list:
    """从手动配置中提取 akshare 函数名"""
    func_names = []
    
    for yaml_file in config_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue
        
        with open(yaml_file) as f:
            config = yaml.safe_load(f)
        
        for interface_name, interface_def in config.items():
            sources = interface_def.get("sources", [])
            for source in sources:
                func = source.get("func")
                if func and func not in func_names:
                    func_names.append(func)
    
    return func_names


def load_manual_config(config_dir: Path) -> dict:
    """加载手动配置"""
    config = {}
    
    for yaml_file in config_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue
        
        with open(yaml_file) as f:
            file_config = yaml.safe_load(f)
        
        config.update(file_config)
    
    return config


def generate_skeleton_from_probed(
    func_name: str,
    func_info: dict,
    probed_schema: dict,
    inferrer: SemanticInferrer,
) -> dict:
    """从探测结果生成骨架"""
    
    # 推断 input 字段
    input_fields = []
    for param in func_info.get("signature", []):
        input_fields.append({
            "name": param["name"],
            "type": param["type"],
            "required": param["required"],
            "desc": func_info.get("doc", {}).get("params", {}).get(param["name"], ""),
        })
    
    # 推断 output 字段
    output_fields = []
    for col in probed_schema.get("columns", []):
        original_name = col["name"]
        inferred_name = inferrer.infer_field_name(original_name)
        
        output_fields.append({
            "name": inferred_name,
            "type": col["type"],
            "desc": f"{original_name} field",
            "original_name": original_name,
        })
    
    return {
        "name": func_name,
        "category": infer_category(func_name),
        "description": func_info.get("doc", {}).get("description", ""),
        "input": input_fields,
        "output": output_fields,
        "sources": [{
            "name": infer_source_name(func_name),
            "func": func_name,
            "enabled": True,
            "input_mapping": {p["name"]: p["name"] for p in input_fields},
            "output_mapping": {
                col["original_name"]: col["name"]
                for col in output_fields
                if col["original_name"] != col["name"]
            },
        }],
    }


def infer_category(func_name: str) -> str:
    """推断分类"""
    if "stock" in func_name.lower():
        return "equity"
    elif "fund" in func_name.lower() or "etf" in func_name.lower():
        return "fund"
    elif "bond" in func_name.lower():
        return "bond"
    elif "index" in func_name.lower():
        return "index"
    elif "futures" in func_name.lower():
        return "futures"
    elif "option" in func_name.lower():
        return "options"
    elif "macro" in func_name.lower() or "economic" in func_name.lower():
        return "macro"
    else:
        return "other"


def infer_source_name(func_name: str) -> str:
    """推断数据源名称"""
    if func_name.endswith("_sina"):
        return "akshare_sina"
    elif func_name.endswith("_em"):
        return "akshare_em"
    elif func_name.endswith("_ths"):
        return "akshare_ths"
    else:
        return "akshare_em"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upgrade manual config")
    parser.add_argument(
        "--manual-config",
        type=Path,
        default=Path("config/interfaces"),
        help="Manual config directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("config/upgraded"),
        help="Output directory",
    )
    parser.add_argument(
        "--probe-limit",
        type=int,
        default=100,
        help="Limit number of functions to probe",
    )
    
    args = parser.parse_args()
    
    args.output.mkdir(parents=True, exist_ok=True)
    
    result_files = upgrade_config(
        args.manual_config,
        args.output,
        args.probe_limit,
    )
    
    print("\n=== Upgrade Complete ===")
    print("Generated files:")
    for name, path in result_files.items():
        print(f"  {name}: {path}")