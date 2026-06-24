"""Float64 快速 DSL。

Float64 quick DSL for building polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flt64QuickDsl:
    """Float64 快速 DSL 入口。

    Quick DSL entry point for building Float64 polynomial
    expressions with concise syntax.

    Attributes:
        namespace: 变量命名空间。/ Variable namespace.
    """

    namespace: str = ""

    def var(self, name: str) -> str:
        """创建变量引用。

        Create a variable reference.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            限定变量名。/ Qualified variable name.
        """
        if self.namespace:
            return f"{self.namespace}.{name}"
        return name

    def constant(self, value: float) -> float:
        """创建常量。

        Create a constant value.

        Args:
            value: 常量值。/ Constant value.

        Returns:
            常量值。/ Constant value.
        """
        return value
