"""对象类别枚举 / Object category enumeration.

定义模型中对象的类别。
Defines the categories of objects within a model.
"""

from __future__ import annotations

import enum


class ObjectCategory(enum.Enum):
    """对象类别 / Object category.

    标识模型元素属于变量、约束还是目标函数。
    Identifies whether a model element is a variable,
    constraint, or objective.

    Attributes:
        value: 类别整数值 / The integer category value.
    """

    VARIABLE = 0
    """变量 / Variable."""

    CONSTRAINT = 1
    """约束 / Constraint."""

    OBJECTIVE = 2
    """目标函数 / Objective."""
