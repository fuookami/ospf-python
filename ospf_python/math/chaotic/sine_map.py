"""混沌：正弦映射。

Chaotic: Sine map.

正弦映射是圆映射的一维变体。
The sine map is a 1D variant of the circle map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SineMap:
    """正弦映射，一维离散混沌系统。

    Sine map, a 1D discrete chaotic system.

    x_{n+1} = a * sin(pi * x_n)

    Attributes:
        a: 控制参数，通常在 (0, 1] 范围内。
            Control parameter, typically in (0, 1].
    """

    a: float = 1.0

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前状态值。/ Current state value.

        Returns:
            下一步的状态值。/ Next state value.
        """
        return self.a * math.sin(math.pi * x)

    def iterate(self, x: float, *, n: int) -> float:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            x: 初始状态值。/ Initial state value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的状态值。/ State value after n steps.
        """
        cx = x
        for _ in range(n):
            cx = self(cx)
        return cx
