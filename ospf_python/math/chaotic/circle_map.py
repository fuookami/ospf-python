"""圆映射。

Circle map (1D map for quasi-periodic systems).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CircleMap:
    """圆映射，一维准周期映射。

    Circle map, a 1D map modeling quasiperiodicity
    and mode locking.

    x_{n+1} = x_n + omega - (k / 2pi) * sin(2pi * x_n)  (mod 1)

    Attributes:
        omega: 频率参数。/ Frequency parameter.
        k: 非线性耦合强度。/ Nonlinear coupling strength.
    """

    omega: float = 0.5
    k: float = 1.0

    def __call__(self, x: float) -> float:
        """执行单步圆映射。

        Perform a single circle map step.

        Args:
            x: 当前相位 [0, 1)。/ Current phase in [0, 1).

        Returns:
            下一相位 [0, 1)。/ Next phase in [0, 1).
        """
        return x + self.omega - self.k / (2.0 * math.pi) * math.sin(2.0 * math.pi * x)

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始相位。/ Initial phase.
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
