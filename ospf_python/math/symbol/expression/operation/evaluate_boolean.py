"""布尔表达式求值。

Boolean expression evaluation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )


def evaluate_boolean(
    expr: Expression,
    bindings: dict[str, Any],
) -> bool:
    """对表达式求值并返回布尔结果。

    Evaluate the expression and return a boolean result.

    Args:
        expr: 待求值的表达式。/ The expression to evaluate.
        bindings: 变量名到值的映射。/ Variable name to value mapping.

    Returns:
        布尔求值结果。/ Boolean evaluation result.
    """
    result = expr.evaluate(bindings)
    return bool(result)
