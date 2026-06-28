"""线性/二次运算操作。

Linear and quadratic polynomial operations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

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


def _extract_quadratic_coefficients(
    polynomial: CanonicalPolynomial,
    variable: str,
) -> tuple[float, float, float]:
    """提取二次方程系数 a, b, c。

    Extract quadratic equation coefficients a, b, c from
    polynomial with respect to variable.

    Args:
        polynomial: 输入多项式。/ Input polynomial.
        variable: 变量名。/ Variable name.

    Returns:
        (a, b, c) 系数元组。/ Coefficient tuple.
    """
    target = _find_symbol(polynomial, variable)
    a = 0.0
    b = 0.0
    c = 0.0
    for term in polynomial.terms:
        power = term.powers.get(target, 0)
        if power == 0:
            # 常数项 / constant term
            c += term.coefficient
        elif power == 1:
            # 线性项系数 / linear term coefficient
            b += term.coefficient
        elif power == 2:
            # 二次项系数 / quadratic term coefficient
            a += term.coefficient
        else:
            raise ValueError(
                f"Degree {power} term found; expected at most degree 2"
            )
    return a, b, c


@dataclass(frozen=True)
class LinearQuadraticOps(Generic[T]):
    """线性/二次多项式运算集。

    Operations specific to linear and quadratic
    polynomials.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def solve_linear(
        self,
        polynomial: T,
        variable: str,
    ) -> float | None:
        """求解线性方程 ax + b = 0。

        Solve linear equation ax + b = 0.

        Args:
            polynomial: 线性多项式。/ Linear polynomial.
            variable: 求解变量。/ Variable to solve.

        Returns:
            解或 None（当 a=0 时）。/ Solution or None (when a=0).
        """
        if isinstance(polynomial, CanonicalPolynomial):
            a, b, c = _extract_quadratic_coefficients(
                polynomial, variable
            )
            if a != 0.0:
                raise ValueError(
                    "Polynomial has quadratic term; "
                    "use solve_quadratic instead"
                )
            if b == 0.0:
                # 无线性项：常数方程 0*x + c = 0
                # 无唯一解（恒等式或矛盾）
                # No linear term: constant equation 0*x + c = 0
                # No unique solution (identity or contradiction)
                return None  # justified: no unique solution for degenerate linear equation
            return -c / b

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def solve_quadratic(
        self,
        polynomial: T,
        variable: str,
    ) -> tuple[float, ...]:
        """求解二次方程 ax^2 + bx + c = 0。

        Solve quadratic equation ax^2 + bx + c = 0.

        Args:
            polynomial: 二次多项式。/ Quadratic polynomial.
            variable: 求解变量。/ Variable to solve.

        Returns:
            解的元组。/ Tuple of solutions.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            a, b, c = _extract_quadratic_coefficients(
                polynomial, variable
            )

            if a == 0.0:
                # 退化为线性方程 / Degenerate to linear
                if b == 0.0:
                    # 常数方程 c = 0：无根或无穷多根
                    # Constant equation c = 0: no root or infinitely many
                    return ()  # justified: degenerate constant equation has no root
                return (-c / b,)

            disc = b * b - 4.0 * a * c
            if disc < 0.0:
                return ()  # justified: no real roots for negative discriminant
            if disc == 0.0:
                return (-b / (2.0 * a),)
            sqrt_disc = math.sqrt(disc)
            return (
                (-b + sqrt_disc) / (2.0 * a),
                (-b - sqrt_disc) / (2.0 * a),
            )

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def discriminant(
        self,
        polynomial: T,
        variable: str,
    ) -> float:
        """计算二次方程判别式 b^2 - 4ac。

        Compute discriminant b^2 - 4ac.

        Args:
            polynomial: 二次多项式。/ Quadratic polynomial.
            variable: 变量名。/ Variable name.

        Returns:
            判别式值。/ Discriminant value.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            a, b, c = _extract_quadratic_coefficients(
                polynomial, variable
            )
            return b * b - 4.0 * a * c

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
