"""标量表达式算术运算构建器。

Scalar expression arithmetic operation builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.symbol.expression.binary_expression import (
    BinaryExpression,
)
from ospf_python.math.symbol.expression.expression_operator import (
    ExpressionOperator,
)
from ospf_python.math.symbol.expression.unary_expression import (
    UnaryExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.scalar_expression import (
        ScalarExpression,
    )


class NumericOps:
    """标量表达式的算术运算构建器。

    Arithmetic operation builder for scalar expressions.

    提供静态方法创建二元和一元算术表达式节点。
    Provides static methods to create binary and unary
    arithmetic expression nodes.
    """

    @staticmethod
    def add_expr(
        lhs: ScalarExpression,
        rhs: ScalarExpression,
    ) -> BinaryExpression:
        """创建加法表达式。/ Create an addition expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            加法二元节点。/ Addition binary node.
        """
        return BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=lhs,
            rhs=rhs,
        )

    @staticmethod
    def sub_expr(
        lhs: ScalarExpression,
        rhs: ScalarExpression,
    ) -> BinaryExpression:
        """创建减法表达式。/ Create a subtraction expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            减法二元节点。/ Subtraction binary node.
        """
        return BinaryExpression(
            op=ExpressionOperator.SUB,
            lhs=lhs,
            rhs=rhs,
        )

    @staticmethod
    def mul_expr(
        lhs: ScalarExpression,
        rhs: ScalarExpression,
    ) -> BinaryExpression:
        """创建乘法表达式。/ Create a multiplication expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            乘法二元节点。/ Multiplication binary node.
        """
        return BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=lhs,
            rhs=rhs,
        )

    @staticmethod
    def div_expr(
        lhs: ScalarExpression,
        rhs: ScalarExpression,
    ) -> BinaryExpression:
        """创建除法表达式。/ Create a division expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            除法二元节点。/ Division binary node.
        """
        return BinaryExpression(
            op=ExpressionOperator.DIV,
            lhs=lhs,
            rhs=rhs,
        )

    @staticmethod
    def neg_expr(
        operand: ScalarExpression,
    ) -> UnaryExpression:
        """创建取负表达式。/ Create a negation expression.

        Args:
            operand: 操作数。/ The operand.

        Returns:
            取负一元节点。/ Negation unary node.
        """
        return UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=operand,
        )
