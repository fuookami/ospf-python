"""电路混沌模型。

Circuit chaotic model (generic chaotic circuit).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class CircuitChaotic:
    """电路混沌模型，通用混沌电路系统。

    Circuit chaotic model, a generic chaotic electronic
    circuit modeled as a 3D ODE system.

    dx/dt = alpha * (y - g(x))
    dy/dt = x - y + z
    dz/dt = -beta * y - gamma * z

    其中 g(x) 为非线性电阻特性。

    Attributes:
        alpha: alpha 参数。/ Alpha parameter.
        beta: beta 参数。/ Beta parameter.
        gamma: gamma 参数。/ Gamma parameter.
        a: 非线性斜率 a。/ Nonlinear slope a.
        b: 非线性斜率 b。/ Nonlinear slope b.
        dt: 时间步长。/ Time step.
    """

    alpha: float = 10.0
    beta: float = 14.0
    gamma: float = 0.1
    a: float = -1.0
    b: float = -0.5
    dt: float = 0.005

    def _g(self, x: float) -> float:
        """计算非线性函数 g(x)。

        Compute nonlinear function g(x).

        Args:
            x: 输入值。/ Input value.

        Returns:
            g(x) 的值。/ Value of g(x).
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
        dx = self.alpha * (y_ - self._g(x_))
        dy = x_ - y_ + z_
        dz = -self.beta * y_ - self.gamma * z_
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
