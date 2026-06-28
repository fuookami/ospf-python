"""LaTeX 渲染。

LaTeX rendering for polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.canonical_monomial import (
        CanonicalMonomial,
    )

T = TypeVar("T")


def _render_monomial_latex(term: CanonicalMonomial, *, is_first: bool) -> str:
    """渲染单项式为 LaTeX。

    Render monomial to LaTeX.

    Args:
        term: 单项式。/ Monomial.
        is_first: 是否为第一个项。/ Whether this is the first term.

    Returns:
        LaTeX 字符串片段。/ LaTeX fragment.
    """
    parts: list[str] = []
    coeff = term.coefficient

    # 渲染变量部分 / Render variable parts
    for sym, power in term.powers.items():
        name = sym.display_name
        # 使用下标表示索引（如果显示名包含下划线后缀）
        # Use subscript for index (if display_name has underscore suffix)
        if power == 1:
            parts.append(name)
        else:
            parts.append(f"{name}^{{{power}}}")

    variable_str = " ".join(parts)

    if not parts:
        # 纯常数项 / Pure constant term
        if is_first:
            return str(coeff) if coeff != 1.0 else "1"
        if coeff > 0:
            return f"+ {coeff}"
        return f"- {abs(coeff)}"

    # 有变量部分 / Has variable parts
    if abs(coeff - 1.0) < 1e-15:
        # 系数为 1 / Coefficient is 1
        if is_first:
            return variable_str
        return f"+ {variable_str}"
    if abs(coeff + 1.0) < 1e-15:
        # 系数为 -1 / Coefficient is -1
        if is_first:
            return f"-{variable_str}"
        return f"- {variable_str}"

    # 一般系数 / General coefficient
    if is_first:
        if coeff < 0:
            return f"-{abs(coeff)} {variable_str}"
        return f"{coeff} {variable_str}"
    if coeff > 0:
        return f"+ {coeff} {variable_str}"
    return f"- {abs(coeff)} {variable_str}"


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
        if isinstance(polynomial, CanonicalPolynomial):
            if polynomial.is_zero:
                return "0"

            # 按次数降序排列后渲染 / Sort by degree descending, then render
            sorted_terms = sorted(
                polynomial.terms,
                key=lambda t: t.degree,
                reverse=True,
            )

            parts: list[str] = []
            for i, term in enumerate(sorted_terms):
                # 跳过零系数项 / Skip zero-coefficient terms
                if abs(term.coefficient) < 1e-15:
                    continue
                latex = _render_monomial_latex(term, is_first=(i == 0 and not parts))
                if latex:
                    parts.append(latex)

            return " ".join(parts) if parts else "0"

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

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
