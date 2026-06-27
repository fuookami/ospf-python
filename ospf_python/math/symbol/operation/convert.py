"""多项式类型转换。

Convert between polynomial types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.monomial.linear_monomial import LinearMonomial
from ospf_python.math.symbol.monomial.quadratic_monomial import (
    QuadraticMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.polynomial.linear_polynomial import (
    LinearPolynomial,
)
from ospf_python.math.symbol.polynomial.quadratic_polynomial import (
    QuadraticPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")
U = TypeVar("U")


def _canonical_to_linear(source: CanonicalPolynomial) -> LinearPolynomial:
    """标准多项式转线性多项式。

    Convert canonical polynomial to linear polynomial.

    Args:
        source: 标准多项式。/ Canonical polynomial.

    Returns:
        线性多项式。/ Linear polynomial.
    """
    linear_terms: list[LinearMonomial] = []
    constant = 0.0
    for term in source.terms:
        if term.is_constant:
            constant += term.coefficient
        elif term.degree == 1 and len(term.powers) == 1:
            symbol = next(iter(term.powers))
            linear_terms.append(
                LinearMonomial.create(
                    symbol=symbol,
                    coefficient=term.coefficient,
                )
            )
        else:
            raise ValueError(
                f"Cannot convert degree-{term.degree} term to linear: {term}"
            )
    return LinearPolynomial(terms=linear_terms, constant=constant)


def _canonical_to_quadratic(
    source: CanonicalPolynomial,
) -> QuadraticPolynomial:
    """标准多项式转二次多项式。

    Convert canonical polynomial to quadratic polynomial.

    Args:
        source: 标准多项式。/ Canonical polynomial.

    Returns:
        二次多项式。/ Quadratic polynomial.
    """
    quadratic_terms: list[QuadraticMonomial] = []
    linear_terms: dict[Symbol, float] = {}
    constant = 0.0
    for term in source.terms:
        if term.is_constant:
            constant += term.coefficient
        elif term.degree == 1 and len(term.powers) == 1:
            symbol = next(iter(term.powers))
            linear_terms[symbol] = (
                linear_terms.get(symbol, 0.0) + term.coefficient
            )
        elif term.degree == 2:
            symbols = list(term.powers.keys())
            powers = list(term.powers.values())
            if len(symbols) == 1 and powers[0] == 2:
                # x^2 项 / x^2 term
                quadratic_terms.append(
                    QuadraticMonomial.create(
                        coefficient=term.coefficient,
                        lhs=symbols[0],
                        rhs=symbols[0],
                    )
                )
            elif len(symbols) == 2 and powers == [1, 1]:
                # x*y 项 / x*y term
                quadratic_terms.append(
                    QuadraticMonomial.create(
                        coefficient=term.coefficient,
                        lhs=symbols[0],
                        rhs=symbols[1],
                    )
                )
            else:
                raise ValueError(
                    f"Cannot convert term to quadratic: {term}"
                )
        else:
            raise ValueError(
                f"Cannot convert degree-{term.degree} term to quadratic: {term}"
            )
    return QuadraticPolynomial(
        quadratic_terms=quadratic_terms,
        linear_terms=linear_terms,
        constant=constant,
    )


def _linear_to_canonical(source: LinearPolynomial) -> CanonicalPolynomial:
    """线性多项式转标准多项式。

    Convert linear polynomial to canonical polynomial.

    Args:
        source: 线性多项式。/ Linear polynomial.

    Returns:
        标准多项式。/ Canonical polynomial.
    """
    terms: list[CanonicalMonomial] = []
    for term in source.terms:
        terms.append(
            CanonicalMonomial.single(
                symbol=term.symbol,
                coefficient=term.coefficient,
            )
        )
    if source.constant != 0.0:
        terms.append(CanonicalMonomial.constant(source.constant))
    return CanonicalPolynomial(terms=terms)


def _quadratic_to_canonical(
    source: QuadraticPolynomial,
) -> CanonicalPolynomial:
    """二次多项式转标准多项式。

    Convert quadratic polynomial to canonical polynomial.

    Args:
        source: 二次多项式。/ Quadratic polynomial.

    Returns:
        标准多项式。/ Canonical polynomial.
    """
    terms: list[CanonicalMonomial] = []
    for term in source.quadratic_terms:
        terms.append(
            CanonicalMonomial(
                coefficient=term.coefficient,
                powers={term.lhs: 1, term.rhs: 1},
            )
        )
    for symbol, coeff in source.linear_terms.items():
        terms.append(
            CanonicalMonomial.single(symbol=symbol, coefficient=coeff)
        )
    if source.constant != 0.0:
        terms.append(CanonicalMonomial.constant(source.constant))
    return CanonicalPolynomial(terms=terms)


@dataclass(frozen=True)
class PolynomialConverter(Generic[T, U]):
    """多项式类型转换器。

    Converts between different polynomial types.

    Attributes:
        source_factory: 源多项式工厂。/ Source factory.
        target_factory: 目标多项式工厂。/ Target factory.
    """

    source_factory: type[T]
    target_factory: type[U]

    def convert(self, source: T) -> U:
        """将源多项式转换为目标类型。

        Convert source polynomial to target type.

        Args:
            source: 源多项式。/ Source polynomial.

        Returns:
            目标类型的多项式。/ Target polynomial.
        """
        target = self.target_factory

        # CanonicalPolynomial -> LinearPolynomial
        if isinstance(source, CanonicalPolynomial) and target is LinearPolynomial:
            return _canonical_to_linear(source)  # type: ignore[return-value]

        # CanonicalPolynomial -> QuadraticPolynomial
        if isinstance(source, CanonicalPolynomial) and target is QuadraticPolynomial:
            return _canonical_to_quadratic(source)  # type: ignore[return-value]

        # LinearPolynomial -> CanonicalPolynomial
        if isinstance(source, LinearPolynomial) and target is CanonicalPolynomial:
            return _linear_to_canonical(source)  # type: ignore[return-value]

        # QuadraticPolynomial -> CanonicalPolynomial
        if isinstance(source, QuadraticPolynomial) and target is CanonicalPolynomial:
            return _quadratic_to_canonical(source)  # type: ignore[return-value]

        # 同类型直接返回 / Same type, return as-is
        if isinstance(source, target):
            return source

        raise TypeError(
            f"Cannot convert {type(source).__name__} "
            f"to {target.__name__}"
        )
