"""混沌：Rayleigh-Benard 吸引子。

Chaotic: Rayleigh-Benard attractor.

Rayleigh-Benard 对流模型的混沌行为。
Chaotic behavior of the Rayleigh-Benard convection model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RayleighBenardAttractor:
    """Rayleigh-Benard 吸引子，描述热对流的混沌系统。

    Rayleigh-Benard attractor describing chaotic thermal convection.

    dx/dt = -sigma * x + sigma * y
    dy/dt = r * x - y - x * z
    dz/dt = -b * z + x * y

    Attributes:
        sigma: Prandtl 数。/ Prandtl number.
        r: Rayleigh 数。/ Rayleigh number.
        b: 几何参数。/ Geometric parameter.
        dt: 时间步长。/ Time step.
    """

    sigma: float = 10.0
    r: float = 28.0
    b: float = 8.0 / 3.0
    dt: float = 0.001

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
        dx = -self.sigma * x + self.sigma * y
        dy = self.r * x - y - x * z
        dz = -self.b * z + x * y
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
