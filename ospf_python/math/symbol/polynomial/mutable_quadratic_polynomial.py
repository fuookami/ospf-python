"""可变二次多项式。

Mutable quadratic polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.math.symbol.polynomial.quadratic_polynomial import (
    QuadraticPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.quadratic_monomial import (
        QuadraticMonomial,
    )
    from ospf_python.math.symbol.symbol import Symbol


@dataclass
class MutableQuadraticPolynomial:
    """可变二次多项式，支持就地添加和移除项。

    Mutable quadratic polynomial supporting in-place
    term addition and removal.

    Attributes:
        _quadratic_terms: 二次单项式列表。/ Quadratic monomial list.
        _linear_terms: 线性项映射。/ Linear terms mapping.
        _constant: 常数项。/ Constant term.
    """

    _quadratic_terms: list[QuadraticMonomial] = field(
        default_factory=list,
    )
    _linear_terms: dict[Symbol, float] = field(
        default_factory=dict,
    )
    _constant: float = 0.0

    @staticmethod
    def zero() -> MutableQuadraticPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            空可变二次多项式。/ Empty mutable quadratic polynomial.
        """
        return MutableQuadraticPolynomial()

    def add_quadratic_term(self, term: QuadraticMonomial) -> None:
        """添加二次项。/ Add a quadratic term.

        Args:
            term: 待添加的二次项。/ Quadratic term to add.
        """
        self._quadratic_terms.append(term)

    def remove_quadratic_term(self, term: QuadraticMonomial) -> None:
        """移除二次项。/ Remove a quadratic term.

        Args:
            term: 待移除的二次项。/ Quadratic term to remove.
        """
        self._quadratic_terms.remove(term)

    def add_linear_coefficient(self, symbol: Symbol, coefficient: float) -> None:
        """添加或累加线性系数。/ Add or accumulate linear coefficient.

        Args:
            symbol: 符号。/ The symbol.
            coefficient: 系数。/ Coefficient.
        """
        self._linear_terms[symbol] = self._linear_terms.get(symbol, 0.0) + coefficient

    def add_constant(self, value: float) -> None:
        """增加常数项。/ Add to constant term.

        Args:
            value: 增加的常数值。/ Constant value to add.
        """
        self._constant += value

    def clear(self) -> None:
        """清空所有项。/ Clear all terms."""
        self._quadratic_terms.clear()
        self._linear_terms.clear()
        self._constant = 0.0

    @property
    def quadratic_terms(self) -> list[QuadraticMonomial]:
        """获取二次项列表的副本。/ Get copy of quadratic terms."""
        return list(self._quadratic_terms)

    @property
    def linear_terms(self) -> dict[Symbol, float]:
        """获取线性项映射的副本。/ Get copy of linear terms."""
        return dict(self._linear_terms)

    @property
    def constant(self) -> float:
        """获取常数项。/ Get constant term."""
        return self._constant

    @property
    def degree(self) -> int:
        """获取多项式次数。/ Get polynomial degree.

        Returns:
            最高次数。/ Maximum degree.
        """
        if self._quadratic_terms:
            return 2
        if self._linear_terms:
            return 1
        return 0

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return (
            len(self._quadratic_terms) == 0
            and len(self._linear_terms) == 0
            and self._constant == 0.0
        )

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号（去重）。/ Get all symbols (deduplicated)."""
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self._quadratic_terms:
            for sym in term.symbols:
                if sym not in seen:
                    seen.add(sym)
                    result.append(sym)
        for sym in self._linear_terms:
            if sym not in seen:
                seen.add(sym)
                result.append(sym)
        return result

    def evaluate(self, bindings: dict[Symbol, float]) -> float:
        """在给定绑定下求值。/ Evaluate under given bindings.

        Args:
            bindings: 符号到值的绑定。/ Symbol-to-value bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        result = self._constant
        for term in self._quadratic_terms:
            lhs_val = bindings.get(term.lhs, 0.0)
            rhs_val = bindings.get(term.rhs, 0.0)
            result += term.evaluate(lhs_val, rhs_val)
        for symbol, coeff in self._linear_terms.items():
            result += coeff * bindings.get(symbol, 0.0)
        return result

    def to_immutable(self) -> QuadraticPolynomial:
        """转换为不可变多项式。/ Convert to immutable polynomial.

        Returns:
            不可变二次多项式。/ Immutable quadratic polynomial.
        """
        return QuadraticPolynomial(
            quadratic_terms=list(self._quadratic_terms),
            linear_terms=dict(self._linear_terms),
            constant=self._constant,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        parts: list[str] = []
        for t in self._quadratic_terms:
            parts.append(str(t))
        for sym, coeff in self._linear_terms.items():
            if coeff == 1.0:
                parts.append(str(sym))
            else:
                parts.append(f"{coeff} * {sym}")
        if self._constant != 0.0 or not parts:
            parts.append(str(self._constant))
        return " + ".join(parts)
