"""混沌：Thomas 循环对称吸引子。

Chaotic: Thomas cyclically symmetric attractor.

Thomas 循环对称吸引子具有完全的循环对称性。
Thomas cyclically symmetric attractor has
full cyclic symmetry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ThomasCyclicallySymmetricAttractor:
    """Thomas 循环对称吸引子，三维混沌系统。

    Thomas cyclically symmetric attractor, a 3D chaotic system.

    dx/dt = sin(y) - b * x
    dy/dt = sin(z) - b * y
    dz/dt = sin(x) - b * z

    与 ThomasAttractor 相同方程，但默认参数不同，
    强调循环对称性。
    Same equations as ThomasAttractor but with different
    defaults emphasizing cyclic symmetry.

    Attributes:
        b: 阻尼参数。/ Damping parameter.
        dt: 时间步长。/ Time step.
    """

    b: float = 0.18
    dt: float = 0.05

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
        dx = math.sin(y) - self.b * x
        dy = math.sin(z) - self.b * y
        dz = math.sin(x) - self.b * z
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
