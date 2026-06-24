"""LaTeX 运算操作。

LaTeX operations for polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.operation.latex import (
        LatexRenderer,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class LatexOps(Generic[T]):
    """LaTeX 运算操作集。

    Collection of LaTeX operations.

    Attributes:
        renderer: LaTeX 渲染器。/ LaTeX renderer.
    """

    renderer: LatexRenderer[T]

    def to_latex(self, polynomial: T) -> str:
        """转换为 LaTeX 格式。

        Convert to LaTeX format.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            LaTeX 字符串。/ LaTeX string.
        """
        return self.renderer.render(polynomial)
