"""代码解析器 - 从源代码中解析 DataFrame 列名"""

from __future__ import annotations

import inspect
import re
import string
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Set

# Python 关键字和内置名称，不应作为字段名
PYTHON_RESERVED = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
PYTHON_RESERVED.update({
    "self", "cls", "args", "kwargs", "result", "results", "data", "df", "ret",
    "response", "json_data", "temp", "tmp", "url", "params", "headers",
})

# 噪声字段模式：纯符号、单字符（除常见列名外）、无意义字符串
NOISE_PATTERNS = [
    re.compile(r'^[_\-\[\]\{\}\(\)\*\+\=\/\\]+$'),  # 纯符号
    re.compile(r'^[a-z]$'),  # 单小写字母（但保留常见列名）
    re.compile(r'^\d+$'),  # 纯数字
    re.compile(r'^[a-z]\d$'),  # 单字母+数字（如 f1, s2）
]

# 允许的单字符列名（常见）
ALLOWED_SINGLE_CHARS = {"c", "p", "v", "t", "n", "o", "h", "l", "d", "a", "b", "s"}


@dataclass
class ParsedColumn:
    """解析出的列信息"""
    name: str
    inferred_type: str = "str"
    source: str = "code_parse"
    description: str = ""


class CodeParser:
    """从源代码解析 DataFrame 列名"""

    RETURN_DOC_PATTERNS = [
        # 原始模式
        re.compile(r':return:.*?DataFrame.*?columns?.*?\[([^\]]+)\]', re.DOTALL),
        # 支持表格格式: | 列1 | 列2 |
        re.compile(r':return:.*?DataFrame.*?\n((?:\|.*\|\n?)+)', re.DOTALL),
        # 支持列表格式: - 列名：说明
        re.compile(r':return:.*?DataFrame.*?\n((?:\s*[-*]\s+\S+[：:].*\n?)+)', re.DOTALL),
    ]

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
        columns.extend(self._parse_rename_columns(source))
        columns.extend(self._parse_dict_columns(source))

        deduped = self._deduplicate(columns)
        filtered = self._filter_noise(deduped)
        return filtered

    def _parse_df_assignment(self, source: str) -> List[ParsedColumn]:
        """解析 DataFrame 赋值中的列名"""
        columns = []

        patterns = [
            (r'\[\s*"([^"]+)"\s*(?:,\s*"([^"]+)")*\s*\]', 'bracket_array'),
            (r"\.rename\(columns\s*=\s*\{([^}]+)\}", 'rename'),
            (r'\.columns\s*=\s*\[([^\]]+)\]', 'columns_assignment'),
            # 新增：匹配 pd.DataFrame({...}) 中的键
            (r'pd\.DataFrame\(\s*\{([^}]+)\}', 'dataframe_dict'),
            # 新增：匹配 df[[...]] 选择列
            (r'df\[\[([^\]]+)\]\]', 'df_select_columns'),
            # 新增：匹配 .loc[:, [...]] 或 .iloc[:, [...]]
            (r'\.loc\[.*?,\s*\[([^\]]+)\]\]', 'loc_columns'),
        ]

        for pattern, ptype in patterns:
            for match in re.finditer(pattern, source):
                content = match.group(1)
                if ptype == 'bracket_array':
                    col_names = self._extract_all_quoted_strings(content)
                elif ptype == 'dataframe_dict':
                    col_names = self._extract_dict_keys(content)
                else:
                    col_names = self._extract_bracketed_names(content)
                for name in col_names:
                    col = ParsedColumn(name=name)
                    if self.type_inferrer:
                        col.inferred_type = self.type_inferrer.infer(name)
                    columns.append(col)

        return columns

    def _parse_rename_columns(self, source: str) -> List[ParsedColumn]:
        """解析 .rename(columns={...}) 中的目标列名"""
        columns = []
        pattern = r'\.rename\(columns\s*=\s*\{([^}]+)\}'

        for match in re.finditer(pattern, source):
            content = match.group(1)
            # 提取字典值（目标列名）
            for val_match in re.finditer(r':\s*["\']([^"\']+)["\']', content):
                name = val_match.group(1).strip()
                if name and not name.startswith('#'):
                    col = ParsedColumn(name=name, source="rename_target")
                    if self.type_inferrer:
                        col.inferred_type = self.type_inferrer.infer(name)
                    columns.append(col)

        return columns

    def _parse_dict_columns(self, source: str) -> List[ParsedColumn]:
        """解析字典中的键作为潜在列名"""
        columns = []
        # 匹配常见的列名字典模式
        pattern = r'(?:column[s]?|fields?|output[s]?)\s*=\s*\{([^}]+)\}'

        for match in re.finditer(pattern, source, re.IGNORECASE):
            content = match.group(1)
            col_names = self._extract_dict_keys(content)
            for name in col_names:
                col = ParsedColumn(name=name, source="dict_columns")
                if self.type_inferrer:
                    col.inferred_type = self.type_inferrer.infer(name)
                columns.append(col)

        return columns

    def _extract_dict_keys(self, content: str) -> List[str]:
        """提取字典中的键名"""
        keys = []
        for match in re.finditer(r'["\']([^"\']+)["\']\s*:', content):
            name = match.group(1).strip()
            if name and not name.startswith('#'):
                keys.append(name)
        return keys

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

        for pattern in self.RETURN_DOC_PATTERNS:
            match = pattern.search(source)
            if match:
                content = match.group(1)
                if '|' in content:
                    # 表格格式
                    col_names = self._parse_table_columns(content)
                elif '-' in content or '*' in content:
                    # 列表格式
                    col_names = self._parse_list_columns(content)
                else:
                    # 原始数组格式
                    col_names = self._split_column_list(content)

                for name in col_names:
                    name = name.strip().strip('"').strip("'").strip('|')
                    if name and len(name) > 0:
                        col = ParsedColumn(name=name, description="from :return: docstring")
                        if self.type_inferrer:
                            col.inferred_type = self.type_inferrer.infer(name)
                        columns.append(col)
                break  # 只使用第一个匹配的模式

        return columns

    def _parse_table_columns(self, content: str) -> List[str]:
        """解析表格格式的列名 | 列1 | 列2 |"""
        columns = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('|') and line.endswith('|'):
                # 跳过分隔行
                if re.match(r'^[\|\s\-:]+$', line):
                    continue
                cells = [c.strip() for c in line.split('|') if c.strip()]
                columns.extend(cells)
        return columns

    def _parse_list_columns(self, content: str) -> List[str]:
        """解析列表格式的列名 - 列名：说明"""
        columns = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('-', '*')):
                # 提取冒号前的部分作为列名
                match = re.match(r'^[-*]\s+([^：:]+)[：:]?', line)
                if match:
                    columns.append(match.group(1).strip())
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

    def _filter_noise(self, columns: List[ParsedColumn]) -> List[ParsedColumn]:
        """过滤噪声字段"""
        filtered = []
        for col in columns:
            name = col.name
            if not name:
                continue

            # 过滤纯符号
            if any(p.match(name) for p in NOISE_PATTERNS):
                if name not in ALLOWED_SINGLE_CHARS:
                    continue

            # 过滤 Python 保留字和常见变量名
            if name.lower() in PYTHON_RESERVED:
                continue

            # 过滤过短的无意义字符串（但保留中文字段）
            if len(name) <= 1 and not any('\u4e00' <= c <= '\u9fff' for c in name):
                if name not in ALLOWED_SINGLE_CHARS:
                    continue

            filtered.append(col)

        return filtered

    def _deduplicate(self, columns: List[ParsedColumn]) -> List[ParsedColumn]:
        """去重，保留第一个出现的列"""
        seen: Set[str] = set()
        result = []
        for col in columns:
            if col.name not in seen:
                seen.add(col.name)
                result.append(col)
        return result