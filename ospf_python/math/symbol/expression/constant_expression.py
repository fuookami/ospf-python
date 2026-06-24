"""常量表达式。

Constant expression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ospf_python.math.symbol.expression.scalar_expression import (
    ScalarExpression,
)


@dataclass(frozen=True)
class ConstantExpression(ScalarExpression):
    """常量表达式节点，持有固定值。

    Constant expression node holding a fixed value.

    Attributes:
        value: 常量值。/ The constant value.
    """

    value: Any

    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """返回常量值，忽略绑定。

        Returns the constant value, ignoring bindings.

        Args:
            bindings: 未使用。/ Unused.

        Returns:
            常量值。/ The constant value.
        """
        return self.value

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        return f"Constant({self.value!r})"
