"""转换为多项式。

Convert various representations to polynomial form.
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
from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")
U = TypeVar("U")

# 全局符号索引计数器 / Global symbol index counter
_symbol_counter: int = 0


def _next_symbol(name: str) -> Symbol:
    """创建下一个符号。/ Create next symbol.

    Args:
        name: 符号名称。/ Symbol name.

    Returns:
        新符号。/ New symbol.
    """
    global _symbol_counter
    symbol = Symbol.create(name=name, index=_symbol_counter)
    _symbol_counter += 1
    return symbol


@dataclass(frozen=True)
class ToPolynomial(Generic[T, U]):
    """多项式转换器。

    Converts various representations (matrix, dict, list)
    to polynomial form.

    Attributes:
        factory: 目标多项式工厂。/ Target factory.
    """

    factory: type[T]

    def from_dict(
        self,
        data: dict[str, float],
    ) -> T:
        """从字典（变量名 -> 系数）创建多项式。

        Create polynomial from dict (variable -> coeff).
        每个键值对创建一个线性项 coefficient * variable。
        Each key-value pair creates a linear term
        coefficient * variable.

        Args:
            data: 系数字典。/ Coefficient dict.

        Returns:
            多项式。/ Polynomial.
        """
        if self.factory is CanonicalPolynomial:
            terms: list[CanonicalMonomial] = []
            for name, coeff in data.items():
                if coeff == 0.0:
                    continue
                symbol = _next_symbol(name)
                terms.append(
                    CanonicalMonomial.single(
                        symbol=symbol,
                        coefficient=coeff,
                    )
                )
            return CanonicalPolynomial(terms=terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported factory type: {self.factory}")

    def from_list(
        self,
        coefficients: list[float],
        variable: str,
    ) -> T:
        """从系数列表创建单变量多项式。

        Create single-variable polynomial from coeff list.
        coefficients[i] 对应 variable^i 的系数。
        coefficients[i] is the coefficient of variable^i.

        Args:
            coefficients: 系数列表（低次到高次）。/
                Coefficient list (low to high degree).
            variable: 变量名。/ Variable name.

        Returns:
            多项式。/ Polynomial.
        """
        if self.factory is CanonicalPolynomial:
            symbol = _next_symbol(variable)
            terms: list[CanonicalMonomial] = []
            for power, coeff in enumerate(coefficients):
                if coeff == 0.0:
                    continue
                if power == 0:
                    terms.append(CanonicalMonomial.constant(coeff))
                else:
                    terms.append(
                        CanonicalMonomial.single(
                            symbol=symbol,
                            coefficient=coeff,
                            power=power,
                        )
                    )
            return CanonicalPolynomial(terms=terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported factory type: {self.factory}")
