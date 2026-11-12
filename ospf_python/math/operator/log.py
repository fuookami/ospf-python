"""对数运算符。

Logarithm operators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, SupportsFloat, SupportsIndex

from ospf_python._binding.elementary_operators import ln as _ln
from ospf_python._binding.elementary_operators import log2 as _log2
from ospf_python._binding.elementary_operators import log10 as _log10

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult


def log_op(x: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """计算自然对数。

    Compute the natural logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        ln(x) 的值。/ Value of ln(x).
    """
    return _ln(x)


def log2_op(x: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """计算以 2 为底的对数。

    Compute the base-2 logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        log2(x) 的值。/ Value of log2(x).
    """
    return _log2(x)


def log10_op(x: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """计算以 10 为底的对数。

    Compute the base-10 logarithm.

    Args:
        x: 输入值（正数）。/ Input value (positive).

    Returns:
        log10(x) 的值。/ Value of log10(x).
    """
    return _log10(x)
