"""混沌：Halvorsen 吸引子。

Chaotic: Halvorsen attractor.

Halvorsen 系统是一种具有对称结构的三维混沌吸引子。
Halvorsen system is a 3D chaotic attractor with
symmetric structure.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HalvorsenAttractor:
    """Halvorsen 吸引子，三维混沌系统。

    Halvorsen attractor, a 3D chaotic system.

    dx/dt = -a*x - 4*y - 4*z - y²
    dy/dt = -a*y - 4*z - 4*x - z²
    dz/dt = -a*z - 4*x - 4*y - x²

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        dt: 时间步长。/ Time step.
    """

    a: float = 1.89
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
        dx = -self.a * x - 4.0 * y - 4.0 * z - y * y
        dy = -self.a * y - 4.0 * z - 4.0 * x - z * z
        dz = -self.a * z - 4.0 * x - 4.0 * y - x * x
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
