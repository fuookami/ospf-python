"""表达式值域 / Expression range.

描述表达式取值的上下界。
Describes the lower and upper bounds of an expression's
value range.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionRange:
    """表达式值域 / Expression range.

    用下界和上界表示表达式的可行值范围。
    Represents the feasible value range of an expression
    using lower and upper bounds.

    Attributes:
        lower: 下界 / The lower bound.
        upper: 上界 / The upper bound.
    """

    lower: float
    upper: float
