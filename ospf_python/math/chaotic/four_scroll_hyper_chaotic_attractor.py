"""混沌：四涡卷超混沌吸引子。

Chaotic: Four-scroll hyperchaotic attractor.

四涡卷超混沌系统具有四个涡卷结构和两个正 Lyapunov 指数。
Four-scroll hyperchaotic system with four scroll
structures and two positive Lyapunov exponents.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FourScrollHyperChaoticAttractor:
    """四涡卷超混沌吸引子，四维混沌系统。

    Four-scroll hyperchaotic attractor, a 4D chaotic system.

    dx/dt = a*(y - x) + w
    dy/dt = d*x - x*z + c*y
    dz/dt = x*y - b*z
    dw/dt = -e*y - f*w

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
        c: 控制参数 c。/ Control parameter c.
        d: 控制参数 d。/ Control parameter d.
        e: 控制参数 e。/ Control parameter e.
        f: 控制参数 f。/ Control parameter f.
        dt: 时间步长。/ Time step.
    """

    a: float = 10.0
    b: float = 4.0
    c: float = 1.0
    d: float = 16.0
    e: float = 1.0
    f: float = 0.5
    dt: float = 0.001

    def __call__(
        self,
        x: float,
        y: float,
        z: float,
        w: float,
    ) -> tuple[float, float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前 x 坐标。/ Current x coordinate.
            y: 当前 y 坐标。/ Current y coordinate.
            z: 当前 z 坐标。/ Current z coordinate.
            w: 当前 w 坐标。/ Current w coordinate.

        Returns:
            下一步的 (x, y, z, w)。/ Next (x, y, z, w).
        """
        dx = self.a * (y - x) + w
        dy = self.d * x - x * z + self.c * y
        dz = x * y - self.b * z
        dw = -self.e * y - self.f * w
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            z + dz * self.dt,
            w + dw * self.dt,
        )

    def iterate(
        self,
        x: float,
        y: float,
        z: float,
        w: float,
        *,
        n: int,
    ) -> tuple[float, float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x: 初始 x 坐标。/ Initial x coordinate.
            y: 初始 y 坐标。/ Initial y coordinate.
            z: 初始 z 坐标。/ Initial z coordinate.
            w: 初始 w 坐标。/ Initial w coordinate.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y, z, w)。/ (x, y, z, w) after n steps.
        """
        cx, cy, cz, cw = x, y, z, w
        for _ in range(n):
            cx, cy, cz, cw = self(cx, cy, cz, cw)
        return cx, cy, cz, cw
