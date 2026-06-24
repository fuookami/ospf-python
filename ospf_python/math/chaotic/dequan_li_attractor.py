"""混沌：Dequan-Li 吸引子。

Chaotic: Dequan-Li attractor.

Dequan-Li 系统是一种三维混沌吸引子 (Li, 2008)。
Dequan-Li system is a 3D chaotic attractor (Li, 2008).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DequanLiAttractor:
    """Dequan-Li 吸引子，三维混沌系统。

    Dequan-Li attractor, a 3D chaotic system.

    dx/dt = a*(y - x) + d*x*z
    dy/dt = k*x + f*y - x*z
    dz/dt = c*z + x*y - e*x²

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        d: 控制参数 d。/ Control parameter d.
        k: 控制参数 k。/ Control parameter k.
        f: 控制参数 f。/ Control parameter f.
        c: 控制参数 c。/ Control parameter c.
        e: 控制参数 e。/ Control parameter e.
        dt: 时间步长。/ Time step.
    """

    a: float = 40.0
    d: float = 0.16
    k: float = 55.0
    f: float = 20.0
    c: float = 11.0
    e: float = 0.46
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
        dx = self.a * (y - x) + self.d * x * z
        dy = self.k * x + self.f * y - x * z
        dz = self.c * z + x * y - self.e * x * x
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
