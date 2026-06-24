"""Anishchenko-Astakhov 吸引子。

Anishchenko-Astakhov attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class AnishchenkoAstakhovAttractor:
    """Anishchenko-Astakhov 吸引子。

    Anishchenko-Astakhov chaotic attractor.

    Attributes:
        mu: 控制参数。/ Control parameter.
        dt: 时间步长。/ Time step.
    """

    mu: float = 1.2
    dt: float = 0.01

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y, z]。/ Current state [x, y, z].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_, z_ = x[0], x[1], x[2]
        dx = self.mu * x_ - y_ - x_ * z_
        dy = x_
        dz = -self.z_decay(z_) + self.mu * x_**2
        return x + self.dt * np.array([dx, dy, dz])

    def z_decay(self, z: float) -> float:
        """计算 z 方向衰减项。

        Compute z-direction decay term.

        Args:
            z: z 值。/ z value.

        Returns:
            衰减值。/ Decay value.
        """
        return z * (1.0 - z) if z > 0 else 0.0

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
