"""Chua 电路（变体）。

Chua's circuit variant (dimensionless form).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChuasCircuit:
    """Chua 电路变体，无量纲化形式。

    Chua's circuit variant using dimensionless variables.

    与标准 ChuaCircuit 相比采用不同的参数化方式，
    便于数值仿真。

    Attributes:
        alpha: alpha 参数。/ Alpha parameter.
        beta: beta 参数。/ Beta parameter.
        gamma: gamma 参数。/ Gamma parameter.
        a: 非线性函数参数 a。/ Nonlinear function parameter a.
        b: 非线性函数参数 b。/ Nonlinear function parameter b.
        dt: 时间步长。/ Time step.
    """

    alpha: float = 10.0
    beta: float = 14.87
    gamma: float = 0.0
    a: float = -1.27
    b: float = -0.68
    dt: float = 0.005

    def _f(self, x: float) -> float:
        """计算非线性函数 f(x)。

        Compute nonlinear function f(x).

        Args:
            x: 输入值。/ Input value.

        Returns:
            f(x) 的值。/ Value of f(x).
        """
        return self.b * x + 0.5 * (self.a - self.b) * (abs(x + 1.0) - abs(x - 1.0))

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [x, y, z]。/ Current state [x, y, z].

        Returns:
            下一步状态。/ Next state.
        """
        x_, y_, z_ = x[0], x[1], x[2]
        dx = self.alpha * (y_ - x_ - self._f(x_))
        dy = x_ - y_ + z_
        dz = -(self.beta * y_ + self.gamma * z_)
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
