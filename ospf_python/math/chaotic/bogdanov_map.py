"""Bogdanov 映射。

Bogdanov map (2D chaotic map).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class BogdanovMap:
    """Bogdanov 映射，二维混沌映射。

    Bogdanov map, a 2D chaotic map with parameters
    epsilon and k.

    x_{n+1} = x_n + y_{n+1}
    y_{n+1} = y_n + epsilon * y_n + k * x_n * (x_n - 1) + mu * x_n * y_n

    Attributes:
        epsilon: 控制参数 epsilon。/ Control parameter epsilon.
        k: 控制参数 k。/ Control parameter k.
        mu: 控制参数 mu。/ Control parameter mu.
    """

    epsilon: float = 0.1
    k: float = 1.5
    mu: float = 0.0

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步映射。

        Perform a single map step.

        Args:
            x: 当前状态 [x, y]。/ Current state [x, y].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_ = x[0], x[1]
        new_y = y_ + self.epsilon * y_ + self.k * x_ * (x_ - 1.0) + self.mu * x_ * y_
        new_x = x_ + new_y
        return np.array([new_x, new_y])

    def iterate(
        self,
        x: NDArray[np.float64],
        *,
        n: int,
    ) -> list[NDArray[np.float64]]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始状态。/ Initial state.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间状态的列表。/ List of all intermediate states.
        """
        result = [x.copy()]
        current = x.copy()
        for _ in range(n):
            current = self(current)
            result.append(current.copy())
        return result
