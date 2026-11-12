"""指数运算符。

Exponential operators.
"""

from __future__ import annotations

from numbers import Real
from typing import TYPE_CHECKING, SupportsFloat, SupportsIndex

from ospf_python._binding.elementary_operators import exp as _exp
from ospf_python._binding.elementary_operators import exp2 as _exp2
from ospf_python._binding.elementary_operators import exp10 as _exp10

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult


def exp_op(x: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """计算 e 的 x 次幂。

    Compute e raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        e^x 的值。/ Value of e^x.
    """
    return _exp(x)


def exp2_op(x: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """计算 2 的 x 次幂。

    Compute 2 raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        2^x 的值。/ Value of 2^x.
    """
    return _exp2(x)


def exp10_op(x: Real) -> BindingResult[float]:
    """计算 10 的 x 次幂。

    Compute 10 raised to the power of x.

    Args:
        x: 指数。/ Exponent.

    Returns:
        10^x 的值。/ Value of 10^x.
    """
    return _exp10(x)
