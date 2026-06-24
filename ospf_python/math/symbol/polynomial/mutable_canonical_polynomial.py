"""可变标准多项式。

Mutable canonical polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.canonical_monomial import (
        CanonicalMonomial,
    )
    from ospf_python.math.symbol.symbol import Symbol


@dataclass
class MutableCanonicalPolynomial:
    """可变标准多项式，支持就地添加和移除项。

    Mutable canonical polynomial supporting in-place
    term addition and removal.

    Attributes:
        _terms: 内部单项式列表。/ Internal monomial list.
    """

    _terms: list[CanonicalMonomial] = field(
        default_factory=list,
    )

    @staticmethod
    def zero() -> MutableCanonicalPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            空可变多项式。/ Empty mutable polynomial.
        """
        return MutableCanonicalPolynomial()

    def add_term(self, term: CanonicalMonomial) -> None:
        """添加单项式。/ Add a monomial term.

        Args:
            term: 待添加的单项式。/ Monomial to add.
        """
        self._terms.append(term)

    def remove_term(self, term: CanonicalMonomial) -> None:
        """移除单项式。/ Remove a monomial term.

        Args:
            term: 待移除的单项式。/ Monomial to remove.
        """
        self._terms.remove(term)

    def clear(self) -> None:
        """清空所有项。/ Clear all terms."""
        self._terms.clear()

    @property
    def terms(self) -> list[CanonicalMonomial]:
        """获取单项式列表的副本。/ Get a copy of monomial list.

        Returns:
            单项式列表副本。/ Copy of monomial list.
        """
        return list(self._terms)

    @property
    def degree(self) -> int:
        """获取多项式次数。/ Get polynomial degree.

        Returns:
            最大单项式次数。/ Maximum monomial degree.
        """
        if not self._terms:
            return 0
        return max(t.degree for t in self._terms)

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return len(self._terms) == 0

    @property
    def term_count(self) -> int:
        """获取项数。/ Get term count."""
        return len(self._terms)

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号（去重）。/ Get all symbols (deduplicated)."""
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self._terms:
            for symbol in term.symbols:
                if symbol not in seen:
                    seen.add(symbol)
                    result.append(symbol)
        return result

    def evaluate(self, bindings: dict[Symbol, float]) -> float:
        """在给定绑定下求值。/ Evaluate under given bindings.

        Args:
            bindings: 符号到值的绑定。/ Symbol-to-value bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        return sum(t.evaluate(bindings) for t in self._terms)

    def to_immutable(self) -> CanonicalPolynomial:
        """转换为不可变多项式。/ Convert to immutable polynomial.

        Returns:
            不可变标准多项式。/ Immutable canonical polynomial.
        """
        return CanonicalPolynomial(terms=list(self._terms))

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        if self.is_zero:
            return "0"
        return " + ".join(str(t) for t in self._terms)
