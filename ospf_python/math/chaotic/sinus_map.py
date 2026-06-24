"""混沌：Sinus 映射。

Chaotic: Sinus map.

Sinus 映射是一维离散混沌系统。
Sinus map is a 1D discrete chaotic system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SinusMap:
    """Sinus 映射，一维离散混沌系统。

    Sinus map, a 1D discrete chaotic system.

    x_{n+1} = sin(pi * x_n)

    无参数，固定映射。/ No parameters, fixed map.
    """

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前状态值。/ Current state value.

        Returns:
            下一步的状态值。/ Next state value.
        """
        return math.sin(math.pi * x)

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
