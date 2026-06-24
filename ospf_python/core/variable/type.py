"""变量类型定义 / Variable type definitions."""

from __future__ import annotations

import enum


class VariableType(enum.Enum):
    """变量类型枚举 / Variable type enumeration.

    描述优化模型中变量的取值类型。
    Describes the value type of variables in an optimization model.

    Attributes:
        CONTINUOUS: 连续变量 / Continuous variable.
        INTEGER: 整数变量 / Integer variable.
        BINARY: 二元变量（0 或 1）/ Binary variable (0 or 1).
        SEMI_CONTINUOUS: 半连续变量 / Semi-continuous variable.
        SEMI_INTEGER: 半整数变量 / Semi-integer variable.
    """

    CONTINUOUS = "continuous"
    """连续变量 / Continuous variable."""

    INTEGER = "integer"
    """整数变量 / Integer variable."""

    BINARY = "binary"
    """二元变量（0 或 1）/ Binary variable (0 or 1)."""

    SEMI_CONTINUOUS = "semi_continuous"
    """半连续变量 / Semi-continuous variable."""

    SEMI_INTEGER = "semi_integer"
    """半整数变量 / Semi-integer variable."""
