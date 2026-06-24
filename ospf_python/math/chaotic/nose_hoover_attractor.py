"""混沌系统：Nose-Hoover 吸引子。

Chaotic system: Nose-Hoover attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NoseHooverAttractor:
    """Nose-Hoover 吸引子，用于分子动力学的混沌系统。

    Nose-Hoover attractor, a chaotic system used in
    molecular dynamics.

    微分方程：
    dx/dt = y
    dy/dt = -x + y * z
    dz/dt = 1 - y^2

    Differential equations:
    dx/dt = y
    dy/dt = -x + y * z
    dz/dt = 1 - y^2

    Attributes:
        dt: 时间步长。/ Time step.
    """

    dt: float = 0.01

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
        dx = y
        dy = -x + y * z
        dz = 1.0 - y * y
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
