"""标量表达式抽象基类。

Scalar expression abstract base class.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from ospf_python.math.symbol.expression.expression import (
    Expression,
)


class ScalarExpression(Expression, ABC):
    """标量表达式基类，支持算术运算符重载。

    Scalar expression base class with arithmetic operator overloading.

    运算符返回表达式节点而非计算结果。
    Operators return expression nodes rather than computed results.
    """

    def __add__(self, other: Any) -> ScalarExpression:
        """加法表达式节点。/ Addition expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce(other)
        return BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=self,
            rhs=other_expr,
        )

    def __mul__(self, other: Any) -> ScalarExpression:
        """乘法表达式节点。/ Multiplication expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce(other)
        return BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=self,
            rhs=other_expr,
        )

    def __sub__(self, other: Any) -> ScalarExpression:
        """减法表达式节点。/ Subtraction expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce(other)
        return BinaryExpression(
            op=ExpressionOperator.SUB,
            lhs=self,
            rhs=other_expr,
        )

    def __truediv__(self, other: Any) -> ScalarExpression:
        """除法表达式节点。/ Division expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce(other)
        return BinaryExpression(
            op=ExpressionOperator.DIV,
            lhs=self,
            rhs=other_expr,
        )

    def __neg__(self) -> ScalarExpression:
        """取负表达式节点。/ Negation expression node."""
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )
        from ospf_python.math.symbol.expression.unary_expression import (
            UnaryExpression,
        )

        return UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=self,
        )


def _coerce(value: Any) -> ScalarExpression:
    """将原生值转为常量表达式。

    Coerce a native value to a constant expression.
    """
    from ospf_python.math.symbol.expression.constant_expression import (
        ConstantExpression,
    )

    if isinstance(value, ScalarExpression):
        return value
    return ConstantExpression(value=value)
