"""增强扫描器 - 提取完整函数签名信息"""

from __future__ import annotations

import inspect
import re
import logging
from typing import Any, Callable, Dict, List, Optional
from typing import get_type_hints

import akshare as ak

logger = logging.getLogger("akshare_data")


class EnhancedScanner:
    """增强的 akshare 扫描器，提取完整的函数元信息"""

    def scan_all(self) -> Dict[str, Dict[str, Any]]:
        """扫描所有公开函数"""
        results = {}
        for name, func in inspect.getmembers(ak, inspect.isfunction):
            if name.startswith("_"):
                continue
            if name in ["update_all_data", "version"]:
                continue
            
            results[name] = self._analyze_function_enhanced(name, func)
        
        logger.info(f"Enhanced scan completed: {len(results)} functions")
        return results

    def _analyze_function_enhanced(
        self, name: str, func: Callable
    ) -> Dict[str, Any]:
        """分析单个函数（增强版）"""
        signature = self._extract_full_signature(func)
        doc_info = self._parse_docstring(func)
        
        return {
            "name": name,
            "module": func.__module__,
            "signature": signature,
            "doc": {
                "full": doc_info["full"],
                "description": doc_info["description"],
                "params": doc_info["params"],
                "returns": doc_info["returns"],
            },
            "type_hints": self._extract_type_hints(func),
        }

    def _extract_full_signature(self, func: Callable) -> List[Dict[str, Any]]:
        """提取完整签名信息（包含类型、默认值、文档）"""
        try:
            sig = inspect.signature(func)
            params = []
            
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                
                param_info = {
                    "name": param_name,
                    "type": self._python_type_to_str(param.annotation),
                    "default": self._get_default_value(param.default),
                    "required": param.default == inspect.Parameter.empty,
                }
                
                params.append(param_info)
            
            return params
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to extract signature for {func.__name__}: {e}")
            return []

    def _extract_type_hints(self, func: Callable) -> Dict[str, str]:
        """提取类型提示"""
        try:
            hints = get_type_hints(func)
            return {k: self._python_type_to_str(v) for k, v in hints.items()}
        except Exception:
            return {}

    def _python_type_to_str(self, type_hint: Any) -> str:
        """将 Python 类型转换为字符串"""
        if type_hint == inspect.Parameter.empty:
            return "str"  # 默认类型
        
        type_name = str(type_hint)
        
        # 提取类型名称
        if "str" in type_name:
            return "str"
        elif "int" in type_name:
            return "int"
        elif "float" in type_name:
            return "float"
        elif "bool" in type_name:
            return "bool"
        elif "DataFrame" in type_name:
            return "DataFrame"
        elif "datetime" in type_name.lower():
            return "datetime"
        else:
            return "str"  # 默认

    def _get_default_value(self, default: Any) -> Optional[Any]:
        """获取默认值"""
        if default == inspect.Parameter.empty:
            return None
        return default

    def _parse_docstring(self, func: Callable) -> Dict[str, Any]:
        """解析 docstring 提取结构化信息"""
        doc = inspect.getdoc(func) or ""
        
        result = {
            "full": doc,
            "description": "",
            "params": {},
            "returns": "",
        }
        
        # 提取描述（第一段）
        lines = doc.split("\n")
        desc_lines = []
        for line in lines:
            if line.strip().startswith(":param") or line.strip().startswith(":return"):
                break
            if line.strip():
                desc_lines.append(line.strip())
        result["description"] = " ".join(desc_lines)
        
        # 提取参数说明
        param_pattern = r":param\s+(\w+):\s*(.+?)(?=:param|:type|:return|:rtype|$)"
        for match in re.finditer(param_pattern, doc, re.DOTALL):
            param_name = match.group(1)
            param_desc = match.group(2).strip().replace("\n", " ")
            result["params"][param_name] = param_desc
        
        # 提取返回说明
        return_pattern = r":return:\s*(.+?)(?=:rtype|$)"
        match = re.search(return_pattern, doc, re.DOTALL)
        if match:
            result["returns"] = match.group(1).strip().replace("\n", " ")
        
        return result


if __name__ == "__main__":
    scanner = EnhancedScanner()
    results = scanner.scan_all()
    
    # 示例输出
    import json
    sample = results.get("stock_zh_a_hist", {})
    print(json.dumps(sample, indent=2, ensure_ascii=False))