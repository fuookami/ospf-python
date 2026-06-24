"""更新赋值 / Update assignment.

定义持久化更新操作的赋值表达式。
Defines assignment expressions for persistence update operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UpdateAssignment:
    """更新赋值 / Update assignment.

    表示更新操作中单个字段的赋值。
    Represents a single field assignment in an update operation.

    Attributes:
        field_name: 字段名称 / The field name.
        value: 赋值内容 / The assignment value.
    """

    field_name: str
    value: Any
