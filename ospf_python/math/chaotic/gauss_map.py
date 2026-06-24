"""混沌：Gauss 映射。

Chaotic: Gauss map.

Gauss 映射 x → {1/x} 是连分数理论中的经典离散动力系统。
Gauss map x -> {1/x} is a classical discrete dynamical
system from continued fraction theory.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GaussMap:
    """Gauss 映射，一维离散动力系统。

    Gauss map, a 1D discrete dynamical system.

    x_{n+1} = {1/x_n} = 1/x_n - floor(1/x_n)

    其中 {·} 表示取小数部分。
    Where {·} denotes the fractional part.
    """

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 值（应为正非零值）。
               Current x value (should be positive nonzero).

        Returns:
            下一步的 x 值。/ Next x value.
        """
        inv = 1.0 / x
        return inv - math.floor(inv)

    def iterate(
        self,
        x: float,
        *,
        n: int,
    ) -> float:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            x: 初始 x 值。/ Initial x value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 x 值。/ x value after n steps.
        """
        cx = x
        for _ in range(n):
            cx = self(cx)
        return cx
