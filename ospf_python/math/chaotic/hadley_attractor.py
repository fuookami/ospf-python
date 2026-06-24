"""混沌：Hadley 吸引子。

Chaotic: Hadley attractor.

Hadley 吸引子描述大气环流中的混沌对流模式。
Hadley attractor describes chaotic convection patterns
in atmospheric circulation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HadleyAttractor:
    """Hadley 吸引子，三维混沌系统。

    Hadley attractor, a 3D chaotic system.

    dx/dt = -y² - z² - a*x + a*alpha
    dy/dt = x*y - beta*x*z - y + 1
    dz/dt = beta*x*y + x*z - z

    Attributes:
        a: 阻尼参数。/ Damping parameter.
        alpha: 外部强迫参数。/ External forcing parameter.
        beta: Coriolis 参数。/ Coriolis parameter.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.25
    alpha: float = 0.9
    beta: float = 4.0
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
        dx = -y * y - z * z - self.a * x + self.a * self.alpha
        dy = x * y - self.beta * x * z - y + 1.0
        dz = self.beta * x * y + x * z - z
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
