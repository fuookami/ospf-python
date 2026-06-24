"""混沌系统：Liu-Chen 吸引子。

Chaotic system: Liu-Chen attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiuChenAttractor:
    """Liu-Chen 吸引子，三维混沌系统。

    Liu-Chen attractor, a 3D chaotic system.

    微分方程：
    dx/dt = a * (y - x)
    dy/dt = b * x - k * x * z
    dz/dt = -c * z + x * y

    Differential equations:
    dx/dt = a * (y - x)
    dy/dt = b * x - k * x * z
    dz/dt = -c * z + x * y

    Attributes:
        a: 参数 a。/ Parameter a.
        b: 参数 b。/ Parameter b.
        c: 参数 c。/ Parameter c.
        k: 非线性耦合参数。
            Nonlinear coupling parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 10.0
    b: float = 40.0
    c: float = 2.5
    k: float = 1.0
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
        dx = self.a * (y - x)
        dy = self.b * x - self.k * x * z
        dz = -self.c * z + x * y
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
