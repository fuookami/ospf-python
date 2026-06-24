"""混沌：三涡卷统一混沌系统。

Chaotic: Three-scroll unified chaotic system.

三涡卷统一混沌系统是一种多涡卷混沌吸引子。
Three-scroll unified chaotic system is a multi-scroll
chaotic attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreeScrollUnifiedChaoticSystem:
    """三涡卷统一混沌系统，三维混沌吸引子。

    Three-scroll unified chaotic system, a 3D chaotic attractor.

    dx/dt = a * (y - x) - d * x * z
    dy/dt = b * x - x * z + c * y
    dz/dt = x * y - z

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
        c: 控制参数 c。/ Control parameter c.
        d: 控制参数 d。/ Control parameter d.
        dt: 时间步长。/ Time step.
    """

    a: float = 40.0
    b: float = 55.0
    c: float = 11.0 / 6.0
    d: float = 0.16
    dt: float = 0.0001

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
        dx = self.a * (y - x) - self.d * x * z
        dy = self.b * x - x * z + self.c * y
        dz = x * y - z
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
