"""混沌映射：Martin 迭代。

Chaotic map: Martin iterate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MartinIterate:
    """Martin 迭代，基于正弦函数的一维混沌映射。

    Martin iterate, a 1D chaotic map based on
    the sine function.

    迭代规则：x_{n+1} = sin(a * x_n)

    Iteration rule: x_{n+1} = sin(a * x_n)

    Attributes:
        a: 缩放参数。/ Scaling parameter.
    """

    a: float = 2.0

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Apply one iteration step.

        Args:
            x: 当前状态值。/ Current state value.

        Returns:
            下一步状态值。/ Next state value.
        """
        return math.sin(self.a * x)

    def iterate(
        self,
        x: float,
        *,
        n: int = 100,
    ) -> float:
        """迭代映射 n 次。

        Iterate the map n times.

        Args:
            x: 初始状态值。/ Initial state value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终状态值。/ Final state value.
        """
        result = x
        for _ in range(n):
            result = self(result)
        return result
