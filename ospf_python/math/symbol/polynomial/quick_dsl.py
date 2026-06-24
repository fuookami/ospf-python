"""多项式快速 DSL。

Quick DSL for building polynomials.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.linear_monomial import (
    LinearMonomial,
)
from ospf_python.math.symbol.polynomial.linear_polynomial import (
    LinearPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# 全局符号索引计数器 / Global symbol index counter
_symbol_counter: int = 0


def var(name: str) -> LinearMonomial:
    """创建线性单项式（系数为 1）。

    Create a linear monomial with coefficient 1.

    Args:
        name: 变量名称。/ Variable name.

    Returns:
        线性单项式。/ Linear monomial.
    """
    global _symbol_counter
    symbol = Symbol.create(name=name, index=_symbol_counter)
    _symbol_counter += 1
    return LinearMonomial.create(symbol=symbol)


def const(value: float) -> LinearPolynomial:
    """创建常数多项式。

    Create a constant polynomial.

    Args:
        value: 常数值。/ Constant value.

    Returns:
        常数线性多项式。/ Constant linear polynomial.
    """
    return LinearPolynomial.of_constant(value)


def reset_counter() -> None:
    """重置符号计数器。/ Reset symbol counter."""
    global _symbol_counter
    _symbol_counter = 0
