"""CSV 序列化辅助工具 / CSV serialization helpers.

提供 CSV 格式的序列化和反序列化功能。
Provides serialization and deserialization for CSV format.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Sequence
from typing import Any


def to_csv(
    records: Sequence[Any],
    fields: Sequence[str] | None = None,
    *,
    delimiter: str = ",",
) -> str:
    """将记录序列化为 CSV 文本 / Serialize records to CSV text.

    支持 dataclass 实例和字典。
    Supports dataclass instances and dictionaries.

    Args:
        records: 待序列化的记录序列 / The sequence of records to
            serialize.
        fields: 要包含的字段名列表，None 表示全部 / Field names to
            include, None means all.
        delimiter: 分隔符 / The delimiter character.

    Returns:
        CSV 格式的文本 / CSV formatted text.
    """
    if not records:
        return ""

    # 确定字段列表 / Determine field list
    if fields is None:
        first = records[0]
        if hasattr(first, "__dataclass_fields__"):
            fields = list(first.__dataclass_fields__.keys())
        elif isinstance(first, dict):
            fields = list(first.keys())
        else:
            return ""

    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    writer.writerow(fields)

    for record in records:
        if hasattr(record, "__dataclass_fields__"):
            row = [getattr(record, f) for f in fields]
        elif isinstance(record, dict):
            row = [record.get(f, "") for f in fields]
        else:
            row = []
        writer.writerow(row)

    return output.getvalue()


def from_csv(
    text: str,
    field_types: dict[str, Callable[[str], Any]] | None = None,
    *,
    delimiter: str = ",",
) -> list[dict[str, Any]]:
    """从 CSV 文本反序列化为字典列表 / Deserialize CSV text to a
    list of dictionaries.

    Args:
        text: CSV 格式的文本 / CSV formatted text.
        field_types: 字段类型转换函数映射，键为字段名，值为转换函数。
            Mapping of field names to type conversion functions.
        delimiter: 分隔符 / The delimiter character.

    Returns:
        反序列化的字典列表 / List of deserialized dictionaries.
    """
    if not text.strip():
        return []

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    results: list[dict[str, Any]] = []

    for row in reader:
        record: dict[str, Any] = {}
        for key, value in row.items():
            if field_types and key in field_types:
                try:
                    record[key] = field_types[key](value)
                except (ValueError, TypeError):
                    record[key] = value
            else:
                record[key] = value
        results.append(record)

    return results
