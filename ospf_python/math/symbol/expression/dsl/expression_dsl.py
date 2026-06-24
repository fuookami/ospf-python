"""表达式 DSL 工具类。

Expression DSL utility class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ospf_python.math.symbol.expression.binary_expression import (
    BinaryExpression,
)
from ospf_python.math.symbol.expression.boolean_expression import (
    BooleanExpressionAdapter,
)
from ospf_python.math.symbol.expression.constant_expression import (
    ConstantExpression,
)
from ospf_python.math.symbol.expression.expression_operator import (
    ExpressionOperator,
)
from ospf_python.math.symbol.expression.path_symbol import PathSymbol
from ospf_python.math.symbol.expression.unary_expression import (
    UnaryExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )
    from ospf_python.math.symbol.expression.scalar_expression import (
        ScalarExpression,
    )


class ExpressionDsl:
    """表达式构建 DSL，提供静态工厂方法。

    Expression building DSL with static factory methods.

    用于以声明式风格构建表达式树。
    Used to build expression trees in a declarative style.
    """

    @staticmethod
    def var(name: str) -> PathSymbol:
        """创建变量符号。/ Create a variable symbol.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            路径符号节点。/ Path symbol node.
        """
        return PathSymbol(name=name)

    @staticmethod
    def const(value: Any) -> ConstantExpression:
        """创建常量表达式。/ Create a constant expression.

        Args:
            value: 常量值。/ Constant value.

        Returns:
            常量表达式节点。/ Constant expression node.
        """
        return ConstantExpression(value=value)

    @staticmethod
    def add(
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
    def mul(
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
    def sub(
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
    def div(
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
    def neg(operand: ScalarExpression) -> UnaryExpression:
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

    @staticmethod
    def and_expr(
        lhs: Expression,
        rhs: Expression,
    ) -> BooleanExpressionAdapter:
        """创建逻辑与表达式。/ Create a logical AND expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            逻辑与节点。/ Logical AND node.
        """
        return BooleanExpressionAdapter(
            BinaryExpression(
                op=ExpressionOperator.AND,
                lhs=lhs,
                rhs=rhs,
            )
        )

    @staticmethod
    def or_expr(
        lhs: Expression,
        rhs: Expression,
    ) -> BooleanExpressionAdapter:
        """创建逻辑或表达式。/ Create a logical OR expression.

        Args:
            lhs: 左操作数。/ Left-hand operand.
            rhs: 右操作数。/ Right-hand operand.

        Returns:
            逻辑或节点。/ Logical OR node.
        """
        return BooleanExpressionAdapter(
            BinaryExpression(
                op=ExpressionOperator.OR,
                lhs=lhs,
                rhs=rhs,
            )
        )

    @staticmethod
    def not_expr(operand: Expression) -> BooleanExpressionAdapter:
        """创建逻辑非表达式。/ Create a logical NOT expression.

        Args:
            operand: 操作数。/ The operand.

        Returns:
            逻辑非节点。/ Logical NOT node.
        """
        return BooleanExpressionAdapter(
            UnaryExpression(
                op=ExpressionOperator.NOT,
                operand=operand,
            )
        )
