"""通用对数运算。

Generic logarithm computation.
"""

from typing import SupportsFloat, SupportsIndex

from ospf_python._binding.logarithm import log_base as _log_base
from ospf_python._binding.result import BindingResult


def log_base(
    x: SupportsFloat | SupportsIndex, base: SupportsFloat | SupportsIndex
) -> BindingResult[float]:
    """通过固定Rust计算任意底数对数，保留任意宽整数域。

    Compute an arbitrary-base logarithm through pinned Rust, retaining wide integers.

    Args:
        x: 输入值（正数）。/ Input value (positive).
        base: 底数（正数且不为 1）。/
            Base (positive and not 1).

    Returns:
        包含Float64对数值的既有Result。/ Existing Result containing a Float64 logarithm.
    """
    return _log_base(x, base)
