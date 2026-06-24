"""Arnold 舌。

Arnold tongue, describing mode-locking regions in circle map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ArnoldTongue:
    """Arnold 舌，描述圆映射中的锁模区域。

    Arnold tongue, describing synchronization regions
    in the circle map.

    Attributes:
        omega: 频率参数。/ Frequency parameter.
        k: 耦合强度。/ Coupling strength.
    """

    omega: float = 0.0
    k: float = 0.5

    def __call__(self, x: float) -> float:
        """执行单步圆映射。

        Perform a single circle map step.

        Args:
            x: 当前相位。/ Current phase.

        Returns:
            下一相位。/ Next phase.
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
