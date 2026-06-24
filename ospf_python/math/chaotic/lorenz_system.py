"""混沌系统：Lorenz 系统。

Chaotic system: Lorenz system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LorenzSystem:
    """Lorenz 系统，经典三维连续混沌系统。

    Lorenz system, the classic 3D continuous chaotic
    system.

    与 LorenzAttractor 相同的数学模型，提供参数化的
    Lorenz 系统通用接口。

    Same mathematical model as LorenzAttractor,
    providing a generalized interface for the
    parameterized Lorenz system.

    微分方程：
    dx/dt = sigma * (y - x)
    dy/dt = rho * x - y - x * z
    dz/dt = x * y - beta * z

    Differential equations:
    dx/dt = sigma * (y - x)
    dy/dt = rho * x - y - x * z
    dz/dt = x * y - beta * z

    Attributes:
        sigma: Prandtl 数。/ Prandtl number.
        rho: Rayleigh 数。/ Rayleigh number.
        beta: 几何参数。/ Geometric parameter.
        dt: 时间步长。/ Time step.
    """

    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 2.667
    dt: float = 0.005

    def __call__(
        self,
        state: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """执行单步积分。

        Apply one integration step.

        Args:
            state: 当前 (x, y, z) 状态。
                Current (x, y, z) state.

        Returns:
            下一步 (x, y, z) 状态。
            Next (x, y, z) state.
        """
        x, y, z = state
        dx = self.sigma * (y - x)
        dy = self.rho * x - y - x * z
        dz = x * y - self.beta * z
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            z + dz * self.dt,
        )

    def iterate(
        self,
        state: tuple[float, float, float],
        *,
        n: int = 1000,
    ) -> tuple[float, float, float]:
        """迭代系统 n 步。

        Iterate the system n steps.

        Args:
            state: 初始 (x, y, z) 状态。
                Initial (x, y, z) state.
            n: 迭代步数。/ Number of steps.

        Returns:
            最终 (x, y, z) 状态。
            Final (x, y, z) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
