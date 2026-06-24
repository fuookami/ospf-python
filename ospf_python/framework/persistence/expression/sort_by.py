"""排序定义 / Sort by.

定义持久化查询的排序规则。
Defines sort rules for persistence queries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SortBy:
    """排序定义 / Sort by.

    指定查询结果的排序字段和方向。
    Specifies the sort field and direction for query results.

    Attributes:
        field_name: 排序字段名 / The sort field name.
        ascending: 是否升序 / Whether to sort ascending.
    """

    field_name: str
    ascending: bool = True
