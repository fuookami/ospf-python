"""可变合并运算操作。

Mutable combine operations for polynomials.
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


def _multiply_polynomials(
    left: CanonicalPolynomial,
    right: CanonicalPolynomial,
) -> CanonicalPolynomial:
    """多项式乘法（分配律）。

    Polynomial multiplication via distributive property.

    Args:
        left: 左多项式。/ Left polynomial.
        right: 右多项式。/ Right polynomial.

    Returns:
        乘积多项式。/ Product polynomial.
    """
    result_terms: list[CanonicalMonomial] = []
    for lt in left.terms:
        for rt in right.terms:
            result_terms.append(lt * rt)
    return CanonicalPolynomial(terms=result_terms)


@dataclass(frozen=True)
class MutableCombineOps(Generic[T]):
    """可变合并运算操作集。

    Operations for combining polynomials in a mutable
    accumulator pattern.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def sum(self, polynomials: list[T]) -> T:
        """求和多个多项式。

        Sum multiple polynomials.

        Args:
            polynomials: 多项式列表。/ Polynomial list.

        Returns:
            求和结果。/ Sum result.
        """
        if not polynomials:
            if self.factory is CanonicalPolynomial:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]
            raise ValueError("Cannot sum empty list with unknown factory")

        if self.factory is CanonicalPolynomial:
            result = CanonicalPolynomial.zero()
            for poly in polynomials:
                result = result + poly  # type: ignore[operator]
            return result  # type: ignore[return-value]

        raise TypeError(f"Unsupported factory type: {self.factory}")

    def product(self, polynomials: list[T]) -> T:
        """求积多个多项式。

        Compute product of multiple polynomials.

        Args:
            polynomials: 多项式列表。/ Polynomial list.

        Returns:
            求积结果。/ Product result.
        """
        if not polynomials:
            if self.factory is CanonicalPolynomial:
                return CanonicalPolynomial.constant(1.0)  # type: ignore[return-value]
            raise ValueError("Cannot product empty list with unknown factory")

        if self.factory is CanonicalPolynomial:
            result = CanonicalPolynomial.constant(1.0)
            for poly in polynomials:
                result = _multiply_polynomials(result, poly)  # type: ignore[arg-type]
            return result  # type: ignore[return-value]

        raise TypeError(f"Unsupported factory type: {self.factory}")
