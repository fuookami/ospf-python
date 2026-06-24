"""表达式规范化：化简常量子表达式。

Expression normalization: simplify constant sub-expressions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.symbol.expression.binary_expression import (
    BinaryExpression,
)
from ospf_python.math.symbol.expression.boolean_expression import (
    BooleanExpressionAdapter,
)
from ospf_python.math.symbol.expression.constant_expression import (
    ConstantExpression,
)
from ospf_python.math.symbol.expression.path_symbol import PathSymbol
from ospf_python.math.symbol.expression.property_path import (
    PropertyPath,
)
from ospf_python.math.symbol.expression.unary_expression import (
    UnaryExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )


def normalize(expr: Expression) -> Expression:
    """化简常量子表达式为常量节点。

    Simplify constant sub-expressions to constant nodes.

    如果表达式的所有子节点均为常量，则直接求值并返回常量。
    If all child nodes of an expression are constants,
    evaluate directly and return a constant.

    Args:
        expr: 待规范化的表达式。/ The expression to normalize.

    Returns:
        规范化后的表达式。/ Normalized expression.
    """
    if isinstance(expr, (PathSymbol, PropertyPath)):
        return expr

    if isinstance(expr, ConstantExpression):
        return expr

    if isinstance(expr, BinaryExpression):
        norm_lhs = normalize(expr.lhs)
        norm_rhs = normalize(expr.rhs)

        if _is_constant(norm_lhs) and _is_constant(norm_rhs):
            val = expr.evaluate({})
            return ConstantExpression(value=val)

        return BinaryExpression(
            op=expr.op,
            lhs=norm_lhs,
            rhs=norm_rhs,
        )

    if isinstance(expr, UnaryExpression):
        norm_operand = normalize(expr.operand)

        if _is_constant(norm_operand):
            val = expr.evaluate({})
            return ConstantExpression(value=val)

        return UnaryExpression(
            op=expr.op,
            operand=norm_operand,
        )

    if isinstance(expr, BooleanExpressionAdapter):
        norm = normalize(expr._inner)
        if isinstance(norm, BooleanExpressionAdapter):
            return norm
        return BooleanExpressionAdapter(norm)

    return expr


def _is_constant(expr: Expression) -> bool:
    """判断表达式是否为常量。

    Check if an expression is a constant.
    """
    if isinstance(expr, ConstantExpression):
        return True
    if isinstance(expr, (PathSymbol, PropertyPath)):
        return False
    if isinstance(expr, BinaryExpression):
        return _is_constant(expr.lhs) and _is_constant(expr.rhs)
    if isinstance(expr, UnaryExpression):
        return _is_constant(expr.operand)
    return False
