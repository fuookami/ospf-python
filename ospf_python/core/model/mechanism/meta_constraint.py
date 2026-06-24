"""元约束 / Meta constraint.

定义模型注册阶段使用的元约束结构。
Defines the meta constraint structure used during
the model registration phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.core.model.basic.constraint_priority import (
    ConstraintPriority,
)

if TYPE_CHECKING:
    from ospf_python.core.model.basic.constraint_sign import (
        ConstraintSign,
    )


@dataclass(frozen=True)
class MetaConstraint:
    """元约束 / Meta constraint.

    在模型注册阶段使用的约束描述，包含优先级信息。
    A constraint descriptor used during the model registration
    phase, including priority information.

    Attributes:
        name: 约束名称 / The constraint name.
        expr: 约束表达式 / The constraint expression.
        sign: 约束方向 / The constraint sign.
        rhs: 右端项值 / The right-hand side value.
        priority: 约束优先级 / The constraint priority.
    """

    name: str
    expr: object
    sign: ConstraintSign
    rhs: float
    priority: ConstraintPriority = ConstraintPriority.REQUIRED
