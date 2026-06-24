"""Brusselator 化学动力学模型。

Brusselator (chemical kinetics model).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Brusselator:
    """Brusselator，化学反应动力学模型。

    Brusselator, a model for chemical oscillation.

    dx/dt = a - (b + 1) * x + x^2 * y
    dy/dt = b * x - x^2 * y

    Attributes:
        a: 反应物浓度参数 a。/ Reactant concentration a.
        b: 反应物浓度参数 b。/ Reactant concentration b.
        dt: 时间步长。/ Time step.
    """

    a: float = 1.0
    b: float = 3.0
    dt: float = 0.01

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y]。/ Current state [x, y].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_ = x[0], x[1]
        dx = self.a - (self.b + 1.0) * x_ + x_**2 * y_
        dy = self.b * x_ - x_**2 * y_
        return x + self.dt * np.array([dx, dy])

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
