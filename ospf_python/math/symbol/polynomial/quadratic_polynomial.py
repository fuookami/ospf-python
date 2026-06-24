"""二次多项式。

Quadratic polynomial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.quadratic_monomial import (
        QuadraticMonomial,
    )
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class QuadraticPolynomial:
    """二次多项式：二次项列表。

    Quadratic polynomial: list of quadratic terms.

    表达形式: sum(c_i * x_i * y_i) + linear + constant
    Expression form: sum(c_i * x_i * y_i) + linear + constant

    Attributes:
        quadratic_terms: 二次单项式列表。/ List of quadratic monomials.
        linear_terms: 线性项（符号到系数映射）。/ Linear terms mapping.
        constant: 常数项。/ Constant term.
    """

    quadratic_terms: list[QuadraticMonomial] = field(
        default_factory=list,
    )
    linear_terms: dict[Symbol, float] = field(
        default_factory=dict,
    )
    constant: float = 0.0

    @staticmethod
    def zero() -> QuadraticPolynomial:
        """创建零多项式。/ Create zero polynomial.

        Returns:
            零多项式。/ Zero polynomial.
        """
        return QuadraticPolynomial()

    @staticmethod
    def of(
        *quadratic: QuadraticMonomial,
        linear: dict[Symbol, float] | None = None,
        constant: float = 0.0,
    ) -> QuadraticPolynomial:
        """从项列表创建。/ Create from term lists.

        Args:
            *quadratic: 二次单项式序列。/ Quadratic monomial sequence.
            linear: 线性项映射。/ Linear terms mapping.
            constant: 常数项，默认 0.0。/ Constant term, defaults to 0.0.

        Returns:
            二次多项式。/ Quadratic polynomial.
        """
        return QuadraticPolynomial(
            quadratic_terms=list(quadratic),
            linear_terms=dict(linear) if linear else {},
            constant=constant,
        )

    @property
    def degree(self) -> int:
        """获取次数。/ Get polynomial degree.

        Returns:
            最高次数。/ Maximum degree.
        """
        if self.quadratic_terms:
            return 2
        if self.linear_terms:
            return 1
        return 0

    @property
    def is_zero(self) -> bool:
        """是否为零多项式。/ Whether it is zero polynomial."""
        return (
            len(self.quadratic_terms) == 0
            and len(self.linear_terms) == 0
            and self.constant == 0.0
        )

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号（去重）。/ Get all symbols (deduplicated).

        Returns:
            去重后的符号列表。/ Deduplicated symbol list.
        """
        seen: set[Symbol] = set()
        result: list[Symbol] = []
        for term in self.quadratic_terms:
            for sym in term.symbols:
                if sym not in seen:
                    seen.add(sym)
                    result.append(sym)
        for sym in self.linear_terms:
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
        result = self.constant
        for term in self.quadratic_terms:
            lhs_val = bindings.get(term.lhs, 0.0)
            rhs_val = bindings.get(term.rhs, 0.0)
            result += term.evaluate(lhs_val, rhs_val)
        for symbol, coeff in self.linear_terms.items():
            result += coeff * bindings.get(symbol, 0.0)
        return result

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        parts: list[str] = []
        for t in self.quadratic_terms:
            parts.append(str(t))
        for sym, coeff in self.linear_terms.items():
            if coeff == 1.0:
                parts.append(str(sym))
            else:
                parts.append(f"{coeff} * {sym}")
        if self.constant != 0.0 or not parts:
            parts.append(str(self.constant))
        return " + ".join(parts)
