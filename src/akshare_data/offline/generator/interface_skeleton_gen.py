"""Interface Skeleton 生成器"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from akshare_data.offline.generator.name_normalizer import NameNormalizer
from akshare_data.offline.generator.param_transform_rules import ParamTransformRules

logger = logging.getLogger("akshare_data")


class InterfaceSkeletonGenerator:
    """从 registry entry 生成 interface skeleton"""

    def __init__(self):
        self.name_normalizer = NameNormalizer()
        self.param_transform_rules = ParamTransformRules()
        self._source_prefix_map = {
            "stock_": "akshare_sina",
            "fund_etf_": "akshare_em",
            "fund_lof_": "akshare_em",
            "index_": "akshare_em",
            "futures_": "akshare_em",
            "macro_": "akshare_em",
            "bond_": "akshare_em",
            "option_": "akshare_em",
            "currency_": "akshare_em",
            "economy_": "akshare_em",
        }

    def generate(
        self,
        registry_entry: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """生成 interface skeleton"""
        name = registry_entry["name"]
        signature = registry_entry.get("signature", [])
        output_fields = registry_entry.get("output_fields", [])
        category = registry_entry.get("category", "other")

        input_fields = self._generate_input(signature)
        output = self._generate_output(output_fields)
        sources = self._generate_sources(name, signature, output_fields, category)
        param_transforms = self.param_transform_rules.infer(signature, category)

        skeleton = {
            "name": name,
            "category": category,
            "description": self._truncate_description(registry_entry.get("description", "")),
            "input": input_fields,
            "output": output,
            "rate_limit_key": registry_entry.get("rate_limit_key", "default"),
            "sources": sources,
        }

        if output_fields:
            skeleton["_generated_note"] = (
                "# Auto-generated from akshare_registry.yaml\n"
                "# TODO: 审核 output_mapping 和 param_transforms 是否正确\n"
                "# TODO: 根据需要添加 aliases 和 cache_table"
            )

        return skeleton

    def _generate_input(self, signature: List[str]) -> List[Dict]:
        """从 signature 生成 input 字段"""
        result = []
        for param in signature:
            inferred_type = self._infer_param_type(param)
            result.append({
                "name": param,
                "type": inferred_type,
                "required": True,
                "desc": f"{param} parameter",
            })
        return result

    def _generate_output(self, output_fields: List[Dict]) -> List[Dict]:
        """从 output_fields 生成 output"""
        if not output_fields:
            return []

        result = []
        for field in output_fields:
            normalized_name = self.name_normalizer.normalize(field["name"])
            result.append({
                "name": normalized_name,
                "type": field.get("type", "str"),
                "desc": field.get("description", "") or f"{normalized_name} field",
            })
        return result

    def _generate_sources(
        self,
        func_name: str,
        signature: List[str],
        output_fields: List[Dict],
        category: str,
    ) -> List[Dict]:
        """生成 sources 配置"""
        source_name = self._guess_source_name(func_name)

        input_mapping = {}
        for param in signature:
            input_mapping[param] = param

        output_mapping = {}
        for field in output_fields:
            source_col = field["name"]
            target_col = self.name_normalizer.normalize(source_col)
            if source_col != target_col:
                output_mapping[source_col] = target_col

        param_transforms = self.param_transform_rules.infer(signature, category)

        return [{
            "name": source_name,
            "func": func_name,
            "enabled": True,
            "input_mapping": input_mapping,
            "param_transforms": param_transforms,
            "output_mapping": output_mapping if output_mapping else self._auto_output_mapping(output_fields),
            "# TODO_note": "请审核 output_mapping 和 param_transforms 是否正确",
        }]

    def _auto_output_mapping(self, output_fields: List[Dict]) -> Dict[str, str]:
        """自动生成 output_mapping（当字段名已经标准化时）"""
        mapping = {}
        for field in output_fields:
            name = field.get("name", "")
            normalized = self.name_normalizer.normalize(name)
            if name != normalized:
                mapping[name] = normalized
            else:
                mapping[name] = name
        return mapping

    def _guess_source_name(self, func_name: str) -> str:
        """猜测数据源名称

        先检查后缀（如 _sina, _em, _ths），再检查前缀
        """
        func_lower = func_name.lower()

        if func_lower.endswith("_sina"):
            return "akshare_sina"
        if func_lower.endswith("_em"):
            return "akshare_em"
        if func_lower.endswith("_ths"):
            return "akshare_ths"
        if func_lower.endswith("_cninfo"):
            return "akshare_cninfo"
        if func_lower.endswith("_cn"):
            return "akshare_cn"

        for prefix, source in self._source_prefix_map.items():
            if func_name.startswith(prefix):
                return source

        return "akshare_em"

    def _infer_param_type(self, param_name: str) -> str:
        """推断参数类型"""
        date_patterns = ["date", "start", "end", "time", "month", "year"]
        if any(p in param_name.lower() for p in date_patterns):
            return "str"

        float_patterns = ["price", "rate", "ratio", "pct", "amount", "volume"]
        if any(p in param_name.lower() for p in float_patterns):
            return "float"

        int_patterns = ["limit", "count", "page", "size", "num"]
        if any(p in param_name.lower() for p in int_patterns):
            return "int"

        if param_name.lower() in ["symbol", "code", "stock", "fund"]:
            return "str"

        if param_name.lower() in ["adjust", "period", "type", "status"]:
            return "str"

        return "str"

    def _truncate_description(self, desc: str, max_len: int = 200) -> str:
        """截断过长的描述"""
        if not desc:
            return ""
        if len(desc) <= max_len:
            return desc
        return desc[:max_len] + "..."

    def generate_all(
        self,
        registry: Dict[str, Any],
        output_dir: Path,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """生成所有 interface skeletons"""
        output_dir.mkdir(parents=True, exist_ok=True)
        interfaces = registry.get("interfaces", {})
        by_category: Dict[str, List] = {}

        for name, entry in interfaces.items():
            category = entry.get("category", "other")
            if categories and category not in categories:
                continue

            skeleton = self.generate(entry)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, skeleton))

        output_files = {}
        for category, entries in by_category.items():
            output_file = output_dir / f"{category}_skeleton.yaml"
            import yaml
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump({name: entry for name, entry in entries}, f, default_flow_style=False, allow_unicode=True)
            output_files[category] = output_file
            logger.info(f"Generated {len(entries)} skeletons for category '{category}' to {output_file}")

        return output_files