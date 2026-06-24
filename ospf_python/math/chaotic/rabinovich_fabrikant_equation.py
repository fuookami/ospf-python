"""混沌：Rabinovich-Fabrikant 方程。

Chaotic: Rabinovich-Fabrikant equation.

Rabinovich-Fabrikant 系统是一种三维混沌系统。
Rabinovich-Fabrikant system is a 3D chaotic system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RabinovichFabrikantEquation:
    """Rabinovich-Fabrikant 方程，三维混沌系统。

    Rabinovich-Fabrikant equation, a 3D chaotic system.

    dx/dt = y * (z - 1 + x^2) + gamma * x
    dy/dt = x * (3 * z + 1 - x^2) + gamma * y
    dz/dt = -2 * z * (alpha + x * y)

    Attributes:
        alpha: 控制参数 alpha。/ Control parameter alpha.
        gamma: 控制参数 gamma。/ Control parameter gamma.
        dt: 时间步长。/ Time step.
    """

    alpha: float = 1.1
    gamma: float = 0.87
    dt: float = 0.001

    def __call__(
        self,
        x: float,
        y: float,
        z: float,
    ) -> tuple[float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前 x 坐标。/ Current x coordinate.
            y: 当前 y 坐标。/ Current y coordinate.
            z: 当前 z 坐标。/ Current z coordinate.

        Returns:
            下一步的 (x, y, z)。/ Next (x, y, z).
        """
        dx = y * (z - 1 + x * x) + self.gamma * x
        dy = x * (3 * z + 1 - x * x) + self.gamma * y
        dz = -2 * z * (self.alpha + x * y)
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            z + dz * self.dt,
        )

    def iterate(
        self,
        x: float,
        y: float,
        z: float,
        *,
        n: int,
    ) -> tuple[float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x: 初始 x 坐标。/ Initial x coordinate.
            y: 初始 y 坐标。/ Initial y coordinate.
            z: 初始 z 坐标。/ Initial z coordinate.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y, z)。/ (x, y, z) after n steps.
        """
        cx, cy, cz = x, y, z
        for _ in range(n):
            cx, cy, cz = self(cx, cy, cz)
        return cx, cy, cz
