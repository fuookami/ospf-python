"""蔡氏电路。

Chua circuit (electronic chaotic circuit model).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChuaCircuit:
    """蔡氏电路，电子混沌电路模型。

    Chua circuit, an electronic circuit that exhibits
    classic chaotic behavior.

    基于无量纲形式的蔡氏电路方程。

    Attributes:
        alpha: 电容比参数。/ Capacitance ratio.
        beta: 电感参数。/ Inductance parameter.
        m0: 内部段斜率。/ Inner segment slope.
        m1: 外部段斜率。/ Outer segment slope.
        dt: 时间步长。/ Time step.
    """

    alpha: float = 9.0
    beta: float = 14.286
    m0: float = -1.27
    m1: float = -0.68
    dt: float = 0.01

    def _nonlinear(self, v: float) -> float:
        """计算非线性电阻特性。

        Compute nonlinear resistor characteristic.

        Args:
            v: 电压值。/ Voltage value.

        Returns:
            电流值。/ Current value.
        """
        return self.m1 * v + 0.5 * (self.m0 - self.m1) * (abs(v + 1.0) - abs(v - 1.0))

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步演化。

        Perform a single time step.

        Args:
            x: 当前状态 [v1, v2, i_l]。/ Current state [v1, v2, i_l].

        Returns:
            下一步状态。/ Next state.
        """
        v1, v2, i_l = x[0], x[1], x[2]
        dv1 = self.alpha * (v2 - v1 - self._nonlinear(v1))
        dv2 = v1 - v2 + i_l
        di_l = -self.beta * v2
        return x + self.dt * np.array([dv1, dv2, di_l])

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
