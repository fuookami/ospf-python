"""通用对数运算。

Generic logarithm computation.
"""

from __future__ import annotations

import math


def log_base(x: float, base: float) -> float:
    """计算以任意底数的对数。

    Compute the logarithm with an arbitrary base.

    Args:
        x: 输入值（正数）。/ Input value (positive).
        base: 底数（正数且不为 1）。/
            Base (positive and not 1).

    Returns:
        对数值。/ Logarithm value.
    """
    return math.log(x) / math.log(base)
