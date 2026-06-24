"""布尔表达式抽象基类。

Boolean expression abstract base class.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from ospf_python.math.symbol.expression.expression import (
    Expression,
)


class BooleanExpression(Expression, ABC):
    """布尔表达式基类，支持逻辑运算符重载。

    Boolean expression base class with logical operator overloading.
    """

    def __and__(self, other: Any) -> BooleanExpression:
        """逻辑与表达式节点。/ Logical AND expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce_bool(other)
        return BooleanExpressionAdapter(
            BinaryExpression(
                op=ExpressionOperator.AND,
                lhs=self,
                rhs=other_expr,
            )
        )

    def __or__(self, other: Any) -> BooleanExpression:
        """逻辑或表达式节点。/ Logical OR expression node."""
        from ospf_python.math.symbol.expression.binary_expression import (
            BinaryExpression,
        )
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )

        other_expr = _coerce_bool(other)
        return BooleanExpressionAdapter(
            BinaryExpression(
                op=ExpressionOperator.OR,
                lhs=self,
                rhs=other_expr,
            )
        )

    def __invert__(self) -> BooleanExpression:
        """逻辑非表达式节点。/ Logical NOT expression node."""
        from ospf_python.math.symbol.expression.expression_operator import (
            ExpressionOperator,
        )
        from ospf_python.math.symbol.expression.unary_expression import (
            UnaryExpression,
        )

        return BooleanExpressionAdapter(
            UnaryExpression(
                op=ExpressionOperator.NOT,
                operand=self,
            )
        )


class BooleanExpressionAdapter(BooleanExpression):
    """将 Expression 节点适配为 BooleanExpression。

    Adapts an Expression node to BooleanExpression.
    """

    def __init__(self, inner: Expression) -> None:
        self._inner = inner

    def evaluate(self, bindings: dict[str, Any]) -> bool:
        """委托给内部表达式。/ Delegate to inner expression."""
        return self._inner.evaluate(bindings)  # type: ignore[no-any-return]

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        return repr(self._inner)


def _coerce_bool(value: Any) -> Expression:
    """将原生布尔值转为常量表达式。

    Coerce a native boolean to a constant expression.
    """
    from ospf_python.math.symbol.expression.constant_expression import (
        ConstantExpression,
    )

    if isinstance(value, Expression):
        return value
    return ConstantExpression(value=value)
