"""标准多项式。

Canonical polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class CanonicalPolynomial:
    """标准多项式：标准单项式的有序列表。

    Canonical polynomial: ordered list of canonical monomials.

    表达形式: m1 + m2 + m3 + ...
    Expression form: m1 + m2 + m3 + ...

    Attributes:
        terms: 单项式列表。/ List of monomials.
    """

    terms: list[CanonicalMonomial] = field(
        default_factory=list,
    )

    @staticmethod
    def zero() -> CanonicalPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            零多项式。/ Zero polynomial.
        """
        return CanonicalPolynomial(terms=[])

    @staticmethod
    def constant(value: float) -> CanonicalPolynomial:
        """创建常数多项式。/ Create constant polynomial.

        Args:
            value: 常数值。/ Constant value.

        Returns:
            常数多项式。/ Constant polynomial.
        """
        return CanonicalPolynomial(terms=[CanonicalMonomial.constant(value)])

    @staticmethod
    def of(*monomials: CanonicalMonomial) -> CanonicalPolynomial:
        """从单项式列表创建。/ Create from monomial list.

        Args:
            *monomials: 单项式序列。/ Monomial sequence.

        Returns:
            标准多项式。/ Canonical polynomial.
        """
        return CanonicalPolynomial(terms=list(monomials))

    @property
    def degree(self) -> int:
        """获取多项式次数。/ Get polynomial degree.

        Returns:
            最大单项式次数，空多项式返回 0。
            Maximum monomial degree, 0 for empty polynomial.
        """
        if not self.terms:
            return 0
        return max(t.degree for t in self.terms)

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return len(self.terms) == 0

    @property
    def term_count(self) -> int:
        """获取项数。/ Get term count."""
        return len(self.terms)

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号（去重）。/ Get all symbols (deduplicated).

        Returns:
            去重后的符号列表。/ Deduplicated symbol list.
        """
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self.terms:
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
        return sum(t.evaluate(bindings) for t in self.terms)

    def __add__(self, other: CanonicalPolynomial) -> CanonicalPolynomial:
        """多项式加法。/ Polynomial addition."""
        return CanonicalPolynomial(terms=self.terms + other.terms)

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        if self.is_zero:
            return "0"
        return " + ".join(str(t) for t in self.terms)
