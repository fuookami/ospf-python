"""线性约束输入 / Linear constraint input.

定义线性约束构建的输入数据结构。
Defines the input data structure for linear constraint
construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)


@dataclass(frozen=True)
class LinearConstraintInput:
    """线性约束输入 / Linear constraint input.

    用于构建线性约束的参数集合。
    A collection of parameters used to build linear constraints.

    Attributes:
        name: 约束名称 / The constraint name.
        coefficients: 变量系数字典 / Variable coefficient
            dictionary.
        sign: 约束方向 / The constraint sign.
        rhs: 右端项值 / The right-hand side value.
    """

    name: str
    coefficients: dict[str, float] = field(
        default_factory=dict,
    )
    sign: ConstraintSign = ConstraintSign.LE
    rhs: float = 0.0
