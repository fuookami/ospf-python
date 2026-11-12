"""整数幂运算。

Integer power computation.
"""

from typing import SupportsIndex

from ospf_python._binding.integer_power import pow_int as _pow_int
from ospf_python._binding.result import BindingResult


def pow_int(base: SupportsIndex, exp: SupportsIndex) -> BindingResult[int]:
    """通过固定 Rust 内核计算整数的非负整数次幂。

    Compute a nonnegative integer power through the pinned Rust kernel.

    Args:
        base: 底数。/ Base.
        exp: 指数（非负）。/ Exponent (non-negative).

    Returns:
        既有 Result，成功包含精确整数。/ Existing Result containing the exact integer.
    """
    return _pow_int(base, exp)
