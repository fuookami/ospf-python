"""二元表达式节点。

Binary expression node.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ospf_python.math.symbol.expression.expression_operator import (
    ExpressionOperator,
)
from ospf_python.math.symbol.expression.scalar_expression import (
    ScalarExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )

# 运算符到 Python 运算符函数的映射
# Operator to Python operator function mapping
_BINARY_EVAL: dict[ExpressionOperator, Any] = {
    ExpressionOperator.ADD: lambda a, b: a + b,
    ExpressionOperator.SUB: lambda a, b: a - b,
    ExpressionOperator.MUL: lambda a, b: a * b,
    ExpressionOperator.DIV: lambda a, b: a / b,
    ExpressionOperator.AND: lambda a, b: a and b,
    ExpressionOperator.OR: lambda a, b: a or b,
    ExpressionOperator.EQ: lambda a, b: a == b,
    ExpressionOperator.NE: lambda a, b: a != b,
    ExpressionOperator.LT: lambda a, b: a < b,
    ExpressionOperator.LE: lambda a, b: a <= b,
    ExpressionOperator.GT: lambda a, b: a > b,
    ExpressionOperator.GE: lambda a, b: a >= b,
}

# 运算符显示符号 / Operator display symbols
_BINARY_SYMBOL: dict[ExpressionOperator, str] = {
    ExpressionOperator.ADD: "+",
    ExpressionOperator.SUB: "-",
    ExpressionOperator.MUL: "*",
    ExpressionOperator.DIV: "/",
    ExpressionOperator.AND: "&&",
    ExpressionOperator.OR: "||",
    ExpressionOperator.EQ: "==",
    ExpressionOperator.NE: "!=",
    ExpressionOperator.LT: "<",
    ExpressionOperator.LE: "<=",
    ExpressionOperator.GT: ">",
    ExpressionOperator.GE: ">=",
}


@dataclass(frozen=True)
class BinaryExpression(ScalarExpression):
    """二元运算表达式节点。

    Binary operation expression node.

    Attributes:
        op: 运算符。/ The operator.
        lhs: 左操作数。/ Left-hand operand.
        rhs: 右操作数。/ Right-hand operand.
    """

    op: ExpressionOperator
    lhs: Expression
    rhs: Expression

    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """递归求值左右操作数后应用运算符。

        Evaluate left and right operands recursively, then apply operator.

        Args:
            bindings: 变量名到值的映射。/ Variable name to value mapping.

        Returns:
            运算结果。/ Operation result.
        """
        left = self.lhs.evaluate(bindings)
        right = self.rhs.evaluate(bindings)
        return _BINARY_EVAL[self.op](left, right)

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        symbol = _BINARY_SYMBOL.get(self.op, self.op.value)
        return f"({symbol} {self.lhs!r} {self.rhs!r})"
