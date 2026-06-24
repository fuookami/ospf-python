"""路径符号表达式。

Path symbol expression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ospf_python.math.symbol.expression.scalar_expression import (
    ScalarExpression,
)


@dataclass(frozen=True)
class PathSymbol(ScalarExpression):
    """通过名称在绑定中查找值的符号。

    Symbol that looks up its value in bindings by name.

    Attributes:
        name: 变量名称。/ Variable name.
    """

    name: str

    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """从绑定中查找变量值。

        Look up variable value from bindings.

        Args:
            bindings: 变量名到值的映射。/ Variable name to value mapping.

        Returns:
            变量对应的值。/ Value corresponding to the variable.

        Raises:
            KeyError: 变量不在绑定中。/ Variable not in bindings.
        """
        return bindings[self.name]

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        return f"PathSymbol({self.name!r})"
