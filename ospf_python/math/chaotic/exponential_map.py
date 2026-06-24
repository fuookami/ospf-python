"""混沌：指数映射。

Chaotic: Exponential map.

指数映射 x → x * exp(r * (1 - x)) 用于种群动力学建模。
Exponential map x -> x * exp(r * (1 - x)) models
population dynamics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ExponentialMap:
    """指数映射，一维离散动力系统。

    Exponential map, a 1D discrete dynamical system.

    x_{n+1} = x_n * exp(r * (1 - x_n))

    Attributes:
        r: 增长参数。/ Growth parameter.
    """

    r: float = 2.7

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 值。/ Current x value.

        Returns:
            下一步的 x 值。/ Next x value.
        """
        return x * math.exp(self.r * (1.0 - x))

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
