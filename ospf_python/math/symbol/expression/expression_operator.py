"""表达式运算符枚举。

Expression operator enum.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class ExpressionOperator(Enum):
    """表达式运算符。

    Expression operators.

    标量运算: ADD, SUB, MUL, DIV, NEG
    布尔运算: AND, OR, NOT
    比较运算: EQ, NE, LT, LE, GT, GE
    """

    # 标量算术 / Scalar arithmetic
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    NEG = "neg"

    # 布尔逻辑 / Boolean logic
    AND = "and"
    OR = "or"
    NOT = "not"

    # 比较 / Comparison
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
