"""约束方向枚举 / Constraint sign enumeration.

定义线性约束的方向（不等式/等式）。
Defines the direction of linear constraints
(inequality / equality).
"""

from __future__ import annotations

import enum


class ConstraintSign(enum.Enum):
    """约束方向 / Constraint sign.

    表示约束表达式中不等式或等式的方向。
    Represents the direction of an inequality or equality
    in a constraint expression.

    Attributes:
        value: 方向标识字符串 / The direction identifier string.
    """

    LE = "<="
    """小于等于 / Less than or equal to."""

    GE = ">="
    """大于等于 / Greater than or equal to."""

    EQ = "=="
    """等于 / Equal to."""
