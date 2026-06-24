"""混沌系统：Lorenz-84 模型。

Chaotic system: Lorenz-84 model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lorenz84Model:
    """Lorenz-84 模型，简化的大气环流模型。

    Lorenz-84 model, a simplified atmospheric
    circulation model.

    微分方程：
    dx/dt = -y^2 - z^2 - a * x + a * F
    dy/dt = x * y - b * x * z - y + G
    dz/dt = b * x * y + x * z - z

    Differential equations:
    dx/dt = -y^2 - z^2 - a * x + a * F
    dy/dt = x * y - b * x * z - y + G
    dz/dt = b * x * y + x * z - z

    Attributes:
        a: 阻尼参数。/ Damping parameter.
        b: 非线性耦合参数。
            Nonlinear coupling parameter.
        F: 外部强迫参数。
            External forcing parameter.
        G: 外部强迫参数。
            External forcing parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.25
    b: float = 4.0
    F: float = 8.0
    G: float = 1.25
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
        dx = -y * y - z * z - self.a * x + self.a * self.F
        dy = x * y - self.b * x * z - y + self.G
        dz = self.b * x * y + x * z - z
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
