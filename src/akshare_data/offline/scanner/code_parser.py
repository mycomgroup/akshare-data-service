"""代码解析器 - 从源代码中解析 DataFrame 列名"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Set


@dataclass
class ParsedColumn:
    """解析出的列信息"""
    name: str
    inferred_type: str = "str"
    source: str = "code_parse"
    description: str = ""


class CodeParser:
    """从源代码解析 DataFrame 列名"""

    RETURN_DOC_PATTERN = r':return:.*?DataFrame.*?columns?.*?\[([^\]]+)\]'

    def __init__(self, type_inferrer: Optional[Any] = None):
        self.type_inferrer = type_inferrer

    def parse(self, func: Callable) -> List[ParsedColumn]:
        """解析函数返回的列"""
        columns = []

        try:
            source = inspect.getsource(func)
        except (OSError, TypeError):
            return []

        columns.extend(self._parse_df_assignment(source))
        columns.extend(self._parse_return_doc(source))

        deduped = self._deduplicate(columns)
        return deduped

    def _parse_df_assignment(self, source: str) -> List[ParsedColumn]:
        """解析 DataFrame 赋值中的列名"""
        columns = []

        patterns = [
            (r'\[\s*"([^"]+)"\s*(?:,\s*"([^"]+)")*\s*\]', 'bracket_array'),
            (r"\.rename\(columns\s*=\s*\{([^}]+)\}", 'rename'),
            (r'\.columns\s*=\s*\[([^\]]+)\]', 'columns_assignment'),
        ]

        for pattern, ptype in patterns:
            for match in re.finditer(pattern, source):
                content = match.group(1)
                if ptype == 'bracket_array':
                    col_names = self._extract_all_quoted_strings(content)
                else:
                    col_names = self._extract_bracketed_names(content)
                for name in col_names:
                    col = ParsedColumn(name=name)
                    if self.type_inferrer:
                        col.inferred_type = self.type_inferrer.infer(name)
                    columns.append(col)

        return columns

    def _extract_all_quoted_strings(self, content: str) -> List[str]:
        """提取所有带引号的字符串（包括数组中的多个列名）"""
        names = []
        for match in re.finditer(r'["\']([^"\']+)["\']', content):
            name = match.group(1).strip()
            if name and len(name) > 0 and not name.startswith('#'):
                names.append(name)
        return names

    def _parse_return_doc(self, source: str) -> List[ParsedColumn]:
        """从 docstring 的 :return: 部分解析列名"""
        columns = []

        doc_match = re.search(r':return:.*?DataFrame.*?columns?.*?\[([^\]]+)\]', source, re.DOTALL)
        if doc_match:
            content = doc_match.group(1)
            col_names = self._split_column_list(content)
            for name in col_names:
                name = name.strip().strip('"').strip("'")
                if name and len(name) > 0:
                    col = ParsedColumn(name=name, description="from :return: docstring")
                    if self.type_inferrer:
                        col.inferred_type = self.type_inferrer.infer(name)
                    columns.append(col)

        return columns

    def _extract_bracketed_names(self, content: str) -> List[str]:
        """从内容中提取带引号的列名"""
        names = []
        for match in re.finditer(r'["\']([^"\']+)["\']', content):
            name = match.group(1).strip()
            if name and len(name) > 0 and not name.startswith('#'):
                names.append(name)
        return names

    def _split_column_list(self, content: str) -> List[str]:
        """分割列名字符串"""
        content = content.replace('"', '').replace("'", "")
        parts = re.split(r'[,，\s]+', content)
        return [p.strip() for p in parts if p.strip()]

    def _deduplicate(self, columns: List[ParsedColumn]) -> List[ParsedColumn]:
        """去重，保留第一个出现的列"""
        seen: Set[str] = set()
        result = []
        for col in columns:
            if col.name not in seen:
                seen.add(col.name)
                result.append(col)
        return result