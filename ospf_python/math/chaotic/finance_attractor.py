"""混沌：金融吸引子。

Chaotic: Finance attractor.

金融吸引子模型描述金融系统中的混沌波动行为 (Ma & Chen, 2001)。
Finance attractor models chaotic fluctuations in
financial systems (Ma & Chen, 2001).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinanceAttractor:
    """金融吸引子，三维混沌系统。

    Finance attractor, a 3D chaotic system.

    dx/dt = (1/b - a)*x + z + x*y
    dy/dt = -b*y - x²
    dz/dt = -x - c*z

    Attributes:
        a: 储蓄参数。/ Saving parameter.
        b: 消费成本参数。/ Consumption cost parameter.
        c: 弹性需求参数。/ Elastic demand parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.001
    b: float = 0.2
    c: float = 1.1
    dt: float = 0.01

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
        dx = (1.0 / self.b - self.a) * x + z + x * y
        dy = -self.b * y - x * x
        dz = -x - self.c * z
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
