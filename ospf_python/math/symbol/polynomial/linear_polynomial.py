"""线性多项式。

Linear polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.linear_monomial import (
        LinearMonomial,
    )
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class LinearPolynomial:
    """线性多项式：线性项加上常数。

    Linear polynomial: linear terms plus a constant.

    表达形式: c1*x1 + c2*x2 + ... + constant
    Expression form: c1*x1 + c2*x2 + ... + constant

    Attributes:
        terms: 线性单项式列表。/ List of linear monomials.
        constant: 常数项。/ Constant term.
    """

    terms: list[LinearMonomial] = field(
        default_factory=list,
    )
    constant: float = 0.0

    @staticmethod
    def zero() -> LinearPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            零多项式。/ Zero polynomial.
        """
        return LinearPolynomial(terms=[], constant=0.0)

    @staticmethod
    def of_constant(value: float) -> LinearPolynomial:
        """创建常数多项式。/ Create constant polynomial.

        Args:
            value: 常数值。/ Constant value.

        Returns:
            常数多项式。/ Constant polynomial.
        """
        return LinearPolynomial(terms=[], constant=value)

    @staticmethod
    def of(
        *monomials: LinearMonomial,
        constant: float = 0.0,
    ) -> LinearPolynomial:
        """从单项式列表创建。/ Create from monomial list.

        Args:
            *monomials: 线性单项式序列。/ Linear monomial sequence.
            constant: 常数项，默认 0.0。/ Constant term, defaults to 0.0.

        Returns:
            线性多项式。/ Linear polynomial.
        """
        return LinearPolynomial(terms=list(monomials), constant=constant)

    @property
    def degree(self) -> int:
        """获取次数，线性多项式最大为 1。/ Get degree, at most 1 for linear."""
        if self.terms:
            return 1
        return 0

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return len(self.terms) == 0 and self.constant == 0.0

    @property
    def is_constant(self) -> bool:
        """是否为常数多项式。/ Whether it is constant polynomial."""
        return len(self.terms) == 0

    @property
    def term_count(self) -> int:
        """获取项数（不含常数项）。/ Get term count (excluding constant)."""
        return len(self.terms)

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号。/ Get all symbols.

        Returns:
            去重后的符号列表。/ Deduplicated symbol list.
        """
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self.terms:
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
        result = self.constant
        for term in self.terms:
            value = bindings.get(term.symbol, 0.0)
            result += term.evaluate(value)
        return result

    def __add__(self, other: LinearPolynomial) -> LinearPolynomial:
        """多项式加法。/ Polynomial addition."""
        return LinearPolynomial(
            terms=self.terms + other.terms,
            constant=self.constant + other.constant,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        parts: list[str] = [str(t) for t in self.terms]
        if self.constant != 0.0 or not parts:
            parts.append(str(self.constant))
        return " + ".join(parts)
