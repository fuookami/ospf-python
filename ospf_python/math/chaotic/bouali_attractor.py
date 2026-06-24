"""Bouali 吸引子。

Bouali attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class BoualiAttractor:
    """Bouali 吸引子，三维混沌系统。

    Bouali attractor, a 3D chaotic ODE system.

    dx/dt = x * (4 - y) + a * z
    dy/dt = -y * (1 - x^2)
    dz/dt = -x * (1.5 - b * z) - 0.05 * z

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.3
    b: float = 1.0
    dt: float = 0.005

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y, z]。/ Current state [x, y, z].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_, z_ = x[0], x[1], x[2]
        dx = x_ * (4.0 - y_) + self.a * z_
        dy = -y_ * (1.0 - x_**2)
        dz = -x_ * (1.5 - self.b * z_) - 0.05 * z_
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
