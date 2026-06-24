"""混沌系统：Lorenz-96 模型。

Chaotic system: Lorenz-96 model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lorenz96Model:
    """Lorenz-96 模型，用于大气动力学研究的高维混沌系统。

    Lorenz-96 model, a high-dimensional chaotic system
    for atmospheric dynamics research.

    微分方程（对第 i 个变量）：
    dx_i/dt = (x_{i+1} - x_{i-2}) * x_{i-1} - x_i + F

    Differential equation (for the i-th variable):
    dx_i/dt = (x_{i+1} - x_{i-2}) * x_{i-1} - x_i + F

    模拟中使用循环边界条件。
    Cyclic boundary conditions are used.

    Attributes:
        n: 变量个数。/ Number of variables.
        F: 外部强迫参数。/ External forcing parameter.
        dt: 时间步长。/ Time step.
    """

    n: int = 8
    F: float = 8.0
    dt: float = 0.01

    def __call__(
        self,
        state: tuple[float, ...],
    ) -> tuple[float, ...]:
        """执行单步积分。

        Apply one integration step.

        Args:
            state: 当前状态向量，长度为 n。
                Current state vector of length n.

        Returns:
            下一步状态向量。/ Next state vector.
        """
        size = len(state)
        dt = self.dt
        forcing = self.F
        derivs = []
        for i in range(size):
            ip1 = (i + 1) % size
            im1 = (i - 1) % size
            im2 = (i - 2) % size
            d = (state[ip1] - state[im2]) * state[im1]
            derivs.append(d - state[i] + forcing)
        return tuple(state[i] + derivs[i] * dt for i in range(size))

    def iterate(
        self,
        state: tuple[float, ...],
        *,
        n: int = 1000,
    ) -> tuple[float, ...]:
        """迭代系统 n 步。

        Iterate the system n steps.

        Args:
            state: 初始状态向量。
                Initial state vector.
            n: 迭代步数。/ Number of steps.

        Returns:
            最终状态向量。/ Final state vector.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
