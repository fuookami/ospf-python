"""蔡氏吸引子。

Chua attractor (3D ODE system).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChuaAttractor:
    """蔡氏吸引子，三维混沌系统。

    Chua attractor, a 3D chaotic ODE system based on
    Chua's circuit equations.

    h(x) = m1 * x + (m0 - m1) * (|x + 1| - |x - 1|) / 2

    dx/dt = alpha * (y - x - h(x))
    dy/dt = x - y + z
    dz/dt = -beta * y

    Attributes:
        alpha: 参数 alpha。/ Parameter alpha.
        beta: 参数 beta。/ Parameter beta.
        m0: 分段线性斜率 m0。/ Piecewise linear slope m0.
        m1: 分段线性斜率 m1。/ Piecewise linear slope m1.
        dt: 时间步长。/ Time step.
    """

    alpha: float = 15.6
    beta: float = 28.0
    m0: float = -1.143
    m1: float = -0.714
    dt: float = 0.001

    def _h(self, x: float) -> float:
        """计算分段线性函数 h(x)。

        Compute piecewise linear function h(x).

        Args:
            x: 输入值。/ Input value.

        Returns:
            h(x) 的值。/ Value of h(x).
        """
        return self.m1 * x + (self.m0 - self.m1) * (abs(x + 1.0) - abs(x - 1.0)) / 2.0

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y, z]。/ Current state [x, y, z].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_, z_ = x[0], x[1], x[2]
        dx = self.alpha * (y_ - x_ - self._h(x_))
        dy = x_ - y_ + z_
        dz = -self.beta * y_
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
