"""电容方程。

Capacitance equation (chaotic circuit model).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CapacitanceEquation:
    """电容方程，非线性电路混沌模型。

    Capacitance equation for chaotic circuit behavior.

    使用非线性映射描述电容充放电的混沌行为。

    Attributes:
        alpha: 非线性系数。/ Nonlinearity coefficient.
        beta: 阻尼系数。/ Damping coefficient.
    """

    alpha: float = 1.0
    beta: float = 0.5

    def __call__(self, x: float) -> float:
        """执行单步映射。

        Perform a single map step.

        Args:
            x: 当前电压值。/ Current voltage value.

        Returns:
            下一步电压值。/ Next voltage value.
        """
        return self.alpha * math.sin(math.pi * x) + self.beta * x

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始电压值。/ Initial voltage value.
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
