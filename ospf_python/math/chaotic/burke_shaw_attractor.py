"""Burke-Shaw 吸引子。

Burke-Shaw attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class BurkeShawAttractor:
    """Burke-Shaw 吸引子，三维混沌系统。

    Burke-Shaw attractor, a 3D chaotic ODE system.

    dx/dt = -S * (x + y)
    dy/dt = -y - S * x * z
    dz/dt = S * x * y + V

    Attributes:
        s: 参数 S（粘滞参数）。/ Parameter S (viscous).
        v: 参数 V。/ Parameter V.
        dt: 时间步长。/ Time step.
    """

    s: float = 10.0
    v: float = 4.272
    dt: float = 0.001

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y, z]。/ Current state [x, y, z].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_, z_ = x[0], x[1], x[2]
        dx = -self.s * (x_ + y_)
        dy = -y_ - self.s * x_ * z_
        dz = self.s * x_ * y_ + self.v
        return x + self.dt * np.array([dx, dy, dz])

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
