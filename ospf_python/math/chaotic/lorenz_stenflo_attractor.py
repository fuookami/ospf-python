"""混沌系统：Lorenz-Stenflo 吸引子。

Chaotic system: Lorenz-Stenflo attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LorenzStenfloAttractor:
    """Lorenz-Stenflo 吸引子，四维混沌系统。

    Lorenz-Stenflo attractor, a 4D chaotic system.

    微分方程：
    dx/dt = a * (y - x) + d * w
    dy/dt = x * (c - z) - y
    dz/dt = x * y - b * z
    dw/dt = -x - a * w

    Differential equations:
    dx/dt = a * (y - x) + d * w
    dy/dt = x * (c - z) - y
    dz/dt = x * y - b * z
    dw/dt = -x - a * w

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        c: 参数 c。/ Parameter c.
        d: 旋转耦合参数。
            Rotation coupling parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 1.0
    b: float = 0.7
    c: float = 26.0
    d: float = 1.5
    dt: float = 0.005

    def __call__(
        self,
        state: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        """执行单步积分。

        Apply one integration step.

        Args:
            state: 当前 (x, y, z, w) 状态。
                Current (x, y, z, w) state.

        Returns:
            下一步 (x, y, z, w) 状态。
            Next (x, y, z, w) state.
        """
        x, y, z, w = state
        dx = self.a * (y - x) + self.d * w
        dy = x * (self.c - z) - y
        dz = x * y - self.b * z
        dw = -x - self.a * w
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            z + dz * self.dt,
            w + dw * self.dt,
        )

    def iterate(
        self,
        state: tuple[float, float, float, float],
        *,
        n: int = 1000,
    ) -> tuple[float, float, float, float]:
        """迭代系统 n 步。

        Iterate the system n steps.

        Args:
            state: 初始 (x, y, z, w) 状态。
                Initial (x, y, z, w) state.
            n: 迭代步数。/ Number of steps.

        Returns:
            最终 (x, y, z, w) 状态。
            Final (x, y, z, w) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
