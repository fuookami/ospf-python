"""Chen-Celikovsky 吸引子。

Chen-Celikovsky attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChenCelikovskyAttractor:
    """Chen-Celikovsky 吸引子。

    Chen-Celikovsky attractor, a variant of the Chen system.

    dx/dt = a * (y - x)
    dy/dt = -x * z + c * y
    dz/dt = x * y - b * z

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        c: 参数 c。/ Parameter c.
        dt: 时间步长。/ Time step.
    """

    a: float = 36.0
    b: float = 3.0
    c: float = 20.0
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
        dx = self.a * (y_ - x_)
        dy = -x_ * z_ + self.c * y_
        dz = x_ * y_ - self.b * z_
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
