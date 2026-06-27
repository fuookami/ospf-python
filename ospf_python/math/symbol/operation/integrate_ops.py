"""积分运算操作。

Integration operations for polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")


def _find_symbol(polynomial: CanonicalPolynomial, variable: str) -> Symbol:
    """在多项式中查找符号。

    Find symbol in polynomial by name.

    Args:
        polynomial: 输入多项式。/ Input polynomial.
        variable: 变量名。/ Variable name.

    Returns:
        匹配的符号。/ Matching symbol.

    Raises:
        ValueError: 未找到变量。/ Variable not found.
    """
    for symbol in polynomial.symbols:
        if symbol.name == variable or symbol.display_name == variable:
            return symbol
    raise ValueError(f"Variable '{variable}' not found in polynomial")


@dataclass(frozen=True)
class IntegrateOps(Generic[T]):
    """积分运算操作集。

    Collection of integration operations.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def integrate(
        self,
        polynomial: T,
        variable: str,
    ) -> T:
        """对指定变量积分（不定积分）。

        Integrate with respect to a variable
        (indefinite integral).

        对单项式 c * x^p 积分得到 c/(p+1) * x^(p+1)。
        Integrates monomial c * x^p to c/(p+1) * x^(p+1).

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variable: 积分变量。/ Variable to integrate.

        Returns:
            积分后的多项式。/ Integrated polynomial.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            target = _find_symbol(polynomial, variable)
            new_terms: list[CanonicalMonomial] = []
            for term in polynomial.terms:
                power = term.powers.get(target, 0)
                new_coeff = term.coefficient / (power + 1)
                new_powers = dict(term.powers)
                new_powers[target] = power + 1
                new_terms.append(
                    CanonicalMonomial(
                        coefficient=new_coeff,
                        powers=new_powers,
                    )
                )
            return CanonicalPolynomial(terms=new_terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def definite_integrate(
        self,
        polynomial: T,
        variable: str,
        lower: float,
        upper: float,
    ) -> float:
        """计算定积分。

        Compute definite integral by integrating and evaluating
        at bounds: F(upper) - F(lower).

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variable: 积分变量。/ Variable to integrate.
            lower: 积分下限。/ Lower bound.
            upper: 积分上限。/ Upper bound.

        Returns:
            定积分值。/ Definite integral value.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            integrated = self.integrate(polynomial, variable)
            result = float(integrated.evaluate({}))  # type: ignore[attr-defined]
            return result
        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
