"""混沌系统：Newton-Leipnik 吸引子。

Chaotic system: Newton-Leipnik attractor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewtonLeipnikAttractor:
    """Newton-Leipnik 吸引子，三维混沌系统。

    Newton-Leipnik attractor, a 3D chaotic system.

    微分方程：
    dx/dt = -a * x + y + 10 * y * z
    dy/dt = -x - 0.4 * y + 5 * x * z
    dz/dt = b * z - 5 * x * y

    Differential equations:
    dx/dt = -a * x + y + 10 * y * z
    dy/dt = -x - 0.4 * y + 5 * x * z
    dz/dt = b * z - 5 * x * y

    Attributes:
        a: 阻尼参数。/ Damping parameter.
        b: 垂直阻尼参数。
            Vertical damping parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.4
    b: float = 0.175
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
        dx = -self.a * x + y + 10.0 * y * z
        dy = -x - 0.4 * y + 5.0 * x * z
        dz = self.b * z - 5.0 * x * y
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
