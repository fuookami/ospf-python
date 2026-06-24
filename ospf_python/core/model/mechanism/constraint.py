"""约束定义 / Constraint definition.

定义优化模型中的约束结构。
Defines the constraint structure in an optimization model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.basic.constraint_sign import (
        ConstraintSign,
    )


@dataclass(frozen=True)
class Constraint:
    """约束 / Constraint.

    表示一个完整的优化约束：名称、表达式、方向和右端项。
    Represents a complete optimization constraint: name,
    expression, sign, and right-hand side.

    Attributes:
        name: 约束名称 / The constraint name.
        expr: 约束表达式（左端项） / The constraint expression
            (left-hand side).
        sign: 约束方向 / The constraint sign.
        rhs: 右端项值 / The right-hand side value.
    """

    name: str
    expr: object
    sign: ConstraintSign
    rhs: float
