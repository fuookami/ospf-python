"""混沌：Gauss 迭代映射。

Chaotic: Gauss iterated map.

Gauss 迭代映射 x → exp(-alpha * x²) + beta 是基于高斯函数的离散动力系统。
Gauss iterated map x -> exp(-alpha * x²) + beta is a
discrete dynamical system based on the Gaussian function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GaussIteratedMap:
    """Gauss 迭代映射，一维离散动力系统。

    Gauss iterated map, a 1D discrete dynamical system.

    x_{n+1} = exp(-alpha * x_n²) + beta

    Attributes:
        alpha: 高斯宽度参数。/ Gaussian width parameter.
        beta: 偏移参数。/ Offset parameter.
    """

    alpha: float = 6.2
    beta: float = -0.5

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 值。/ Current x value.

        Returns:
            下一步的 x 值。/ Next x value.
        """
        return math.exp(-self.alpha * x * x) + self.beta

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
