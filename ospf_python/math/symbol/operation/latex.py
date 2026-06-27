"""LaTeX 渲染。

LaTeX rendering for polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class LatexRenderer(Generic[T]):
    """LaTeX 渲染器。

    Renders polynomial expressions to LaTeX format.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def render(self, polynomial: T) -> str:
        """将多项式渲染为 LaTeX 字符串。

        Render polynomial to LaTeX string.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            LaTeX 字符串。/ LaTeX string.
        """
        return repr(polynomial)

    def render_inline(self, polynomial: T) -> str:
        """渲染为行内 LaTeX。

        Render as inline LaTeX.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            行内 LaTeX 字符串。/ Inline LaTeX string.
        """
        return f"${self.render(polynomial)}$"

    def render_display(self, polynomial: T) -> str:
        """渲染为展示 LaTeX。

        Render as display LaTeX.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            展示 LaTeX 字符串。/ Display LaTeX string.
        """
        return f"$$\n{self.render(polynomial)}\n$$"
