"""生物学混沌模型。

Biology chaotic model (logistic-like population dynamics).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BiologyChaoticModel:
    """生物学混沌模型，基于种群动力学。

    Biology chaotic model based on population dynamics.

    使用 Ricker 模型: x_{n+1} = x_n * exp(r * (1 - x_n / K)).

    Attributes:
        r: 增长率。/ Growth rate.
        k: 环境容纳量。/ Carrying capacity.
    """

    r: float = 2.5
    k: float = 1.0

    def __call__(self, x: float) -> float:
        """执行单步演化。

        Perform a single step of population update.

        Args:
            x: 当前种群密度。/ Current population density.

        Returns:
            下一步种群密度。/ Next population density.
        """
        return x * math.exp(self.r * (1.0 - x / self.k))

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始种群密度。/ Initial population density.
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
