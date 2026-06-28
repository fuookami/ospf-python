"""符号微分。

Symbolic differentiation of polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Differentiator(Generic[T]):
    """符号微分器。

    Performs symbolic differentiation on polynomials.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def differentiate(
        self,
        polynomial: T,
        variable: str,
    ) -> T:
        """对指定变量求导。

        Differentiate with respect to a variable.

        对单项式 c * x^p 关于 variable 求导：
        - 若 variable 不在单项式中：导数为 0（跳过）
        - 若 power > 0：导数为 c * p * x^(p-1)，其他符号幂次不变

        Differentiate monomial c * x^p w.r.t. variable:
        - If variable not in monomial: derivative is 0 (skip)
        - If power > 0: derivative is c * p * x^(p-1), other symbols unchanged

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variable: 求导变量。/ Variable to diff.

        Returns:
            导数多项式。/ Derivative polynomial.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            new_terms: list[CanonicalMonomial] = []
            for term in polynomial.terms:
                # 查找目标变量在单项式中的幂次
                # Find target variable power in monomial
                target_power = 0
                target_symbol = None
                for sym, pow_val in term.powers.items():
                    if sym.name == variable or sym.display_name == variable:
                        target_power = pow_val
                        target_symbol = sym
                        break

                if target_power == 0 or target_symbol is None:
                    # 不含目标变量的项导数为 0
                    # Terms without target variable contribute 0
                    continue

                # 新系数 = 旧系数 * 幂次
                # New coefficient = old coefficient * power
                new_coefficient = term.coefficient * target_power

                # 新幂次：目标变量幂次减 1
                # New powers: target variable power decremented by 1
                new_powers = dict(term.powers)
                if target_power == 1:
                    del new_powers[target_symbol]
                else:
                    new_powers[target_symbol] = target_power - 1

                new_terms.append(
                    CanonicalMonomial(
                        coefficient=new_coefficient,
                        powers=new_powers,
                    )
                )

            if not new_terms:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]

            return CanonicalPolynomial(terms=new_terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
