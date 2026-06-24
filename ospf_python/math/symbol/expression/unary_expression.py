"""一元表达式节点。

Unary expression node.
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

# 运算符到 Python 函数的映射
# Operator to Python function mapping
_UNARY_EVAL: dict[ExpressionOperator, Any] = {
    ExpressionOperator.NEG: lambda a: -a,
    ExpressionOperator.NOT: lambda a: not a,
}

# 运算符显示符号 / Operator display symbols
_UNARY_SYMBOL: dict[ExpressionOperator, str] = {
    ExpressionOperator.NEG: "-",
    ExpressionOperator.NOT: "!",
}


@dataclass(frozen=True)
class UnaryExpression(ScalarExpression):
    """一元运算表达式节点。

    Unary operation expression node.

    Attributes:
        op: 运算符。/ The operator.
        operand: 操作数。/ The operand.
    """

    op: ExpressionOperator
    operand: Expression

    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """递归求值操作数后应用运算符。

        Evaluate operand recursively, then apply operator.

        Args:
            bindings: 变量名到值的映射。/ Variable name to value mapping.

        Returns:
            运算结果。/ Operation result.
        """
        val = self.operand.evaluate(bindings)
        return _UNARY_EVAL[self.op](val)

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        symbol = _UNARY_SYMBOL.get(self.op, self.op.value)
        return f"({symbol} {self.operand!r})"
