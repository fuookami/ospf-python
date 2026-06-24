"""混沌：Rucklidge 吸引子。

Chaotic: Rucklidge attractor.

Rucklidge 系统描述对流不稳定性中的混沌行为。
Rucklidge system describes chaotic behavior in convective instability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RucklidgeAttractor:
    """Rucklidge 吸引子，三维混沌系统。

    Rucklidge attractor, a 3D chaotic system.

    dx/dt = -kappa * x + alpha * y - y * z
    dy/dt = x
    dz/dt = -z + y^2

    Attributes:
        kappa: 阻尼参数 kappa。/ Damping parameter kappa.
        alpha: 控制参数 alpha。/ Control parameter alpha.
        dt: 时间步长。/ Time step.
    """

    kappa: float = 2.0
    alpha: float = 6.7
    dt: float = 0.005

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
        dx = -self.kappa * x + self.alpha * y - y * z
        dy = x
        dz = -z + y * y
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
