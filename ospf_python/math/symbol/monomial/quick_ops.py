"""单项式快速运算。

Quick monomial operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


def mul_monomials(
    lhs: CanonicalMonomial,
    rhs: CanonicalMonomial,
) -> CanonicalMonomial:
    """两个标准单项式相乘。/ Multiply two canonical monomials.

    Args:
        lhs: 左操作数。/ Left operand.
        rhs: 右操作数。/ Right operand.

    Returns:
        相乘结果。/ Multiplication result.
    """
    merged_powers: dict[Symbol, int] = dict(lhs.powers)
    for symbol, power in rhs.powers.items():
        merged_powers[symbol] = merged_powers.get(symbol, 0) + power
    return CanonicalMonomial(
        coefficient=lhs.coefficient * rhs.coefficient,
        powers=merged_powers,
    )


def divide_monomials(
    lhs: CanonicalMonomial,
    rhs: CanonicalMonomial,
) -> CanonicalMonomial:
    """两个标准单项式相除。/ Divide two canonical monomials.

    Args:
        lhs: 被除数。/ Dividend.
        rhs: 除数。/ Divisor.

    Returns:
        相除结果。/ Division result.
    """
    result_powers: dict[Symbol, int] = dict(lhs.powers)
    for symbol, power in rhs.powers.items():
        current = result_powers.get(symbol, 0)
        new_power = current - power
        if new_power == 0:
            result_powers.pop(symbol, None)
        else:
            result_powers[symbol] = new_power
    coeff = 0.0 if rhs.coefficient == 0.0 else lhs.coefficient / rhs.coefficient
    return CanonicalMonomial(
        coefficient=coeff,
        powers=result_powers,
    )
