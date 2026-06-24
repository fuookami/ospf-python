"""Chebyshev 映射。

Chebyshev map (1D polynomial chaotic map).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ChebyshevMap:
    """Chebyshev 映射，一维多项式混沌映射。

    Chebyshev map, a 1D polynomial chaotic map.

    T_n(x) = cos(n * arccos(x))

    Attributes:
        n: Chebyshev 多项式阶数。/ Chebyshev polynomial degree.
    """

    n: int = 2

    def __call__(self, x: float) -> float:
        """执行单步 Chebyshev 映射。

        Perform a single Chebyshev map step.

        Args:
            x: 当前值，范围 [-1, 1]。/ Current value in [-1, 1].

        Returns:
            映射后的值。/ Mapped value.
        """
        return math.cos(self.n * math.acos(x))

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始值。/ Initial value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间值的列表。/ List of all intermediate values.
        """
        result = [x]
        current = x
        for _ in range(n):
            current = self(current)
            result.append(current)
        return result
