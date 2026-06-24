"""混沌系统：Lorenz Mod-2 吸引子。

Chaotic system: Lorenz Mod-2 attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LorenzMod2Attractor:
    """Lorenz Mod-2 吸引子，Lorenz 系统的另一变体。

    Lorenz Mod-2 attractor, another variant of
    the Lorenz system.

    微分方程：
    dx/dt = -a * x + a * y - y * z
    dy/dt = c * x + d * y + x * z
    dz/dt = -b * z + x * y / 3.0

    Differential equations:
    dx/dt = -a * x + a * y - y * z
    dy/dt = c * x + d * y + x * z
    dz/dt = -b * z + x * y / 3.0

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        c: 参数 c。/ Parameter c.
        d: 参数 d。/ Parameter d.
        dt: 时间步长。/ Time step.
    """

    a: float = 2.0
    b: float = 0.7
    c: float = 15.0
    d: float = -2.0
    dt: float = 0.001

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
        dx = -self.a * x + self.a * y - y * z
        dy = self.c * x + self.d * y + x * z
        dz = -self.b * z + x * y / 3.0
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
