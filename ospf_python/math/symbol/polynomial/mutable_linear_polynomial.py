"""可变线性多项式。

Mutable linear polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.math.symbol.polynomial.linear_polynomial import (
    LinearPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.linear_monomial import (
        LinearMonomial,
    )
    from ospf_python.math.symbol.symbol import Symbol


@dataclass
class MutableLinearPolynomial:
    """可变线性多项式，支持就地添加和移除项。

    Mutable linear polynomial supporting in-place
    term addition and removal.

    Attributes:
        _terms: 内部单项式列表。/ Internal monomial list.
        _constant: 常数项。/ Constant term.
    """

    _terms: list[LinearMonomial] = field(
        default_factory=list,
    )
    _constant: float = 0.0

    @staticmethod
    def zero() -> MutableLinearPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            空可变线性多项式。/ Empty mutable linear polynomial.
        """
        return MutableLinearPolynomial()

    def add_term(self, term: LinearMonomial) -> None:
        """添加线性项。/ Add a linear term.

        Args:
            term: 待添加的线性项。/ Linear term to add.
        """
        self._terms.append(term)

    def remove_term(self, term: LinearMonomial) -> None:
        """移除线性项。/ Remove a linear term.

        Args:
            term: 待移除的线性项。/ Linear term to remove.
        """
        self._terms.remove(term)

    def add_constant(self, value: float) -> None:
        """增加常数项。/ Add to constant term.

        Args:
            value: 增加的常数值。/ Constant value to add.
        """
        self._constant += value

    def clear(self) -> None:
        """清空所有项。/ Clear all terms."""
        self._terms.clear()
        self._constant = 0.0

    @property
    def terms(self) -> list[LinearMonomial]:
        """获取单项式列表的副本。/ Get a copy of monomial list.

        Returns:
            单项式列表副本。/ Copy of monomial list.
        """
        return list(self._terms)

    @property
    def constant(self) -> float:
        """获取常数项。/ Get constant term."""
        return self._constant

    @property
    def degree(self) -> int:
        """获取多项式次数。/ Get polynomial degree.

        Returns:
            有线性项时为 1，否则为 0。
            1 if has linear terms, 0 otherwise.
        """
        if self._terms:
            return 1
        return 0

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return len(self._terms) == 0 and self._constant == 0.0

    @property
    def term_count(self) -> int:
        """获取项数（不含常数项）。/ Get term count (excluding constant)."""
        return len(self._terms)

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号。/ Get all symbols."""
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self._terms:
            if term.symbol not in seen:
                seen.add(term.symbol)
                result.append(term.symbol)
        return result

    def evaluate(self, bindings: dict[Symbol, float]) -> float:
        """在给定绑定下求值。/ Evaluate under given bindings.

        Args:
            bindings: 符号到值的绑定。/ Symbol-to-value bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        result = self._constant
        for term in self._terms:
            value = bindings.get(term.symbol, 0.0)
            result += term.evaluate(value)
        return result

    def to_immutable(self) -> LinearPolynomial:
        """转换为不可变多项式。/ Convert to immutable polynomial.

        Returns:
            不可变线性多项式。/ Immutable linear polynomial.
        """
        return LinearPolynomial(
            terms=list(self._terms),
            constant=self._constant,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        parts: list[str] = [str(t) for t in self._terms]
        if self._constant != 0.0 or not parts:
            parts.append(str(self._constant))
        return " + ".join(parts)
