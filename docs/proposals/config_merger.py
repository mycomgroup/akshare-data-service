"""配置合并器 - 用生成的信息升级手动配置"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from pathlib import Path
import yaml

logger = logging.getLogger("akshare_data")


class ConfigMerger:
    """合并手动配置和生成配置"""

    def __init__(self):
        self.merge_stats = {
            "interfaces_processed": 0,
            "fields_added": 0,
            "type_conflicts": 0,
            "mapping_improved": 0,
        }

    def upgrade_manual_config(
        self,
        manual_config: Dict[str, Any],
        generated_config: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """升级手动配置"""
        changes = []
        upgraded = {}
        
        for interface_name, interface_def in manual_config.items():
            upgraded_def, interface_changes = self._upgrade_interface(
                interface_name,
                interface_def,
                generated_config,
            )
            upgraded[interface_name] = upgraded_def
            changes.extend(interface_changes)
        
        return upgraded, changes

    def _upgrade_interface(
        self,
        interface_name: str,
        interface_def: Dict[str, Any],
        generated_config: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """升级单个接口配置"""
        changes = []
        upgraded = interface_def.copy()
        
        # 1. 找到对应的 generated 接口（通过 sources.func 匹配）
        akshare_func = self._extract_akshare_func(interface_def)
        if not akshare_func:
            return upgraded, [f"{interface_name}: no akshare function found"]
        
        gen_interface = self._find_generated_interface(akshare_func, generated_config)
        if not gen_interface:
            return upgraded, [f"{interface_name}: no matching generated interface"]
        
        # 2. 补充 input 字段
        missing_inputs = self._find_missing_fields(
            upgraded.get("input", []),
            gen_interface.get("input", []),
        )
        if missing_inputs:
            if "input" not in upgraded:
                upgraded["input"] = []
            upgraded["input"].extend(missing_inputs)
            changes.append(
                f"{interface_name}: added {len(missing_inputs)} input fields - "
                f"{[f['name'] for f in missing_inputs]}"
            )
            self.merge_stats["fields_added"] += len(missing_inputs)
        
        # 3. 补充 output 字段
        missing_outputs = self._find_missing_fields(
            upgraded.get("output", []),
            gen_interface.get("output", []),
        )
        if missing_outputs:
            if "output" not in upgraded:
                upgraded["output"] = []
            upgraded["output"].extend(missing_outputs)
            changes.append(
                f"{interface_name}: added {len(missing_outputs)} output fields - "
                f"{[f['name'] for f in missing_outputs]}"
            )
            self.merge_stats["fields_added"] += len(missing_outputs)
        
        # 4. 验证类型一致性
        type_conflicts = self._check_type_conflicts(
            upgraded.get("output", []),
            gen_interface.get("output", []),
        )
        if type_conflicts:
            changes.append(
                f"{interface_name}: type conflicts - {type_conflicts}"
            )
            self.merge_stats["type_conflicts"] += len(type_conflicts)
        
        # 5. 补充 output_mapping
        improved_mappings = self._improve_output_mapping(
            upgraded.get("sources", []),
            gen_interface.get("output", []),
        )
        if improved_mappings:
            changes.append(
                f"{interface_name}: improved output_mapping - {improved_mappings}"
            )
            self.merge_stats["mapping_improved"] += len(improved_mappings)
        
        self.merge_stats["interfaces_processed"] += 1
        return upgraded, changes

    def _extract_akshare_func(self, interface_def: Dict[str, Any]) -> Optional[str]:
        """提取 akshare 函数名"""
        sources = interface_def.get("sources", [])
        for source in sources:
            func = source.get("func")
            if func:
                return func
        return None

    def _find_generated_interface(
        self,
        akshare_func: str,
        generated_config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """在 generated 配置中找到对应的接口"""
        for category, interfaces in generated_config.items():
            for interface_name, interface_def in interfaces.items():
                if interface_name == akshare_func:
                    return interface_def
        return None

    def _find_missing_fields(
        self,
        manual_fields: List[Dict[str, Any]],
        generated_fields: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """找到缺失的字段"""
        manual_names = {f["name"] for f in manual_fields}
        missing = []
        
        for gen_field in generated_fields:
            if gen_field["name"] not in manual_names:
                missing.append(gen_field)
        
        return missing

    def _check_type_conflicts(
        self,
        manual_fields: List[Dict[str, Any]],
        generated_fields: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """检查类型冲突"""
        conflicts = []
        manual_types = {f["name"]: f.get("type") for f in manual_fields}
        
        for gen_field in generated_fields:
            name = gen_field["name"]
            gen_type = gen_field.get("type")
            
            if name in manual_types:
                manual_type = manual_types[name]
                if manual_type != gen_type:
                    conflicts.append({
                        "name": name,
                        "manual_type": manual_type,
                        "generated_type": gen_type,
                    })
        
        return conflicts

    def _improve_output_mapping(
        self,
        sources: List[Dict[str, Any]],
        generated_fields: List[Dict[str, Any]],
    ) -> List[str]:
        """改进 output_mapping"""
        improvements = []
        
        for source in sources:
            output_mapping = source.get("output_mapping", {})
            if not output_mapping:
                # 生成 output_mapping
                new_mapping = {}
                for field in generated_fields:
                    original_name = field.get("original_name", field["name"])
                    normalized_name = field["name"]
                    if original_name != normalized_name:
                        new_mapping[original_name] = normalized_name
                
                if new_mapping:
                    source["output_mapping"] = new_mapping
                    improvements.append(f"added {len(new_mapping)} mappings")
        
        return improvements

    def generate_report(
        self,
        changes: List[str],
        output_path: Path,
    ):
        """生成差异报告"""
        report_lines = [
            "# 配置升级报告",
            "",
            f"## 统计信息",
            f"- 处理接口数: {self.merge_stats['interfaces_processed']}",
            f"- 新增字段数: {self.merge_stats['fields_added']}",
            f"- 类型冲突数: {self.merge_stats['type_conflicts']}",
            f"- 改进映射数: {self.merge_stats['mapping_improved']}",
            "",
            "## 详细变更",
            "",
        ]
        
        for change in changes:
            report_lines.append(f"- {change}")
        
        output_path.write_text("\n".join(report_lines), encoding="utf-8")
        logger.info(f"Report saved to {output_path}")


# 使用示例
if __name__ == "__main__":
    import json
    
    # 示例：升级 stock_daily 配置
    manual_config = {
        "stock_daily": {
            "name": "stock_daily",
            "input": [
                {"name": "symbol", "type": "str", "required": True},
                {"name": "start_date", "type": "date", "required": True},
            ],
            "output": [
                {"name": "date", "type": "date"},
                {"name": "close", "type": "float"},
            ],
            "sources": [
                {"name": "akshare_sina", "func": "stock_zh_a_daily"}
            ],
        }
    }
    
    generated_config = {
        "equity_skeleton": {
            "stock_zh_a_daily": {
                "input": [
                    {"name": "symbol", "type": "str", "required": True},
                    {"name": "start_date", "type": "str", "required": True},
                    {"name": "end_date", "type": "str", "required": True},
                    {"name": "adjust", "type": "str", "required": False},
                ],
                "output": [
                    {"name": "date", "type": "date"},
                    {"name": "open", "type": "float"},
                    {"name": "high", "type": "float"},
                    {"name": "low", "type": "float"},
                    {"name": "close", "type": "float"},
                    {"name": "volume", "type": "float"},
                    {"name": "amount", "type": "float"},
                ],
            }
        }
    }
    
    merger = ConfigMerger()
    upgraded, changes = merger.upgrade_manual_config(manual_config, generated_config)
    
    print("Changes:")
    for change in changes:
        print(f"  - {change}")
    
    print("\nUpgraded config:")
    print(json.dumps(upgraded, indent=2, ensure_ascii=False))