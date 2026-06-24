"""Aizawa 吸引子。

Aizawa attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class AizawaAttractor:
    """Aizawa 吸引子，三维常微分方程系统。

    Aizawa attractor, a 3D chaotic ODE system.

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        c: 参数 c。/ Parameter c.
        d: 参数 d。/ Parameter d.
        e: 参数 e。/ Parameter e.
        f: 参数 f。/ Parameter f.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.95
    b: float = 0.7
    c: float = 0.6
    d: float = 3.5
    e: float = 0.25
    f: float = 0.1
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
        dx = (z_ - self.b) * x_ - self.d * y_
        dy = self.d * x_ + (z_ - self.b) * y_
        dz = (
            self.c
            + self.a * z_
            - z_**3 / 3.0
            - (x_**2 + y_**2) * (1.0 + self.e * z_)
            + self.f * z_ * x_**3
        )
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
