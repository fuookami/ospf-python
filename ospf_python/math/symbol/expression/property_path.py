"""属性路径表达式。

Property path expression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ospf_python.math.symbol.expression.scalar_expression import (
    ScalarExpression,
)


@dataclass(frozen=True)
class PropertyPath(ScalarExpression):
    """通过路径链访问嵌套属性的表达式。

    Expression that accesses nested attributes via a path chain.

    路径中的每个段依次用于 getattr 或 dict 查找。
    Each segment in the path is used for getattr or dict lookup in order.

    Attributes:
        path: 属性路径段的元组。/ Tuple of attribute path segments.
    """

    path: tuple[str, ...]

    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """沿路径链逐段解析嵌套值。

        Resolve nested value by following path segments.

        先在绑定中查找第一段，后续段通过 getattr 或 dict 访问。
        First segment is looked up in bindings; subsequent segments
        use getattr or dict access.

        Args:
            bindings: 变量名到值的映射。/ Variable name to value mapping.

        Returns:
            路径末端的值。/ Value at the end of the path.
        """
        current = bindings[self.path[0]]
        for segment in self.path[1:]:
            if isinstance(current, dict):
                current = current[segment]
            else:
                current = getattr(current, segment)
        return current

    def __repr__(self) -> str:
        """开发者友好表示。/ Developer-friendly representation."""
        return f"PropertyPath({'.'.join(self.path)})"
