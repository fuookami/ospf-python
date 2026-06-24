"""混沌：Sakarya 吸引子。

Chaotic: Sakarya attractor.

Sakarya 系统是一种三维混沌吸引子。
Sakarya system is a 3D chaotic attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SakaryaAttractor:
    """Sakarya 吸引子，三维混沌系统。

    Sakarya attractor, a 3D chaotic system.

    dx/dt = -x + y + y * z
    dy/dt = -x - y + a * x * z
    dz/dt = z - b * x * y

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.4
    b: float = 0.2
    dt: float = 0.005

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
        dx = -x + y + y * z
        dy = -x - y + self.a * x * z
        dz = z - self.b * x * y
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
