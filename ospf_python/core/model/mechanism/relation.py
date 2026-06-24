"""关系定义 / Relation definition.

定义模型对象之间的关系。
Defines relationships between model objects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Relation:
    """关系 / Relation.

    表示两个模型对象之间的关联关系。
    Represents an association relationship between two
    model objects.

    Attributes:
        source: 源对象名称 / The source object name.
        target: 目标对象名称 / The target object name.
        relation_type: 关系类型 / The relation type.
    """

    source: str
    target: str
    relation_type: str = ""
