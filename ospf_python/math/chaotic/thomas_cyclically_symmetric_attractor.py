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
        # 决定 5 / B309：以 `ospf-kotlin` 为准。`ThomasCyclicallySymmetricAttractor.kt`
        # 的步进也是对角式（与 `ThomasAttractor.kt` 相同），原式是循环式。
        # Unified with `ospf-kotlin` (B309): its step is also the diagonal form, same as
        # `ThomasAttractor.kt`; the shipped form was cyclically shifted.
        # 决定 5 / B311：**回到标准 Thomas 循环式**。线上权威（Wikipedia 的
        # "Thomas' cyclically symmetric attractor" 与 deeptime 文档）给出的正是
        # `ẋ=sin(y)−bx`、`ẏ=sin(z)−by`、`ż=sin(x)−bz`；
        # `ospf-kotlin` 与上游 Rust 用的是对角式，偏离标准，需改它们。
        # Back to the STANDARD cyclic Thomas form (B311). Wikipedia and deeptime both give
        # dx=sin(y)-bx, dy=sin(z)-by, dz=sin(x)-bz; ospf-kotlin and Rust use the diagonal form
        # and are the ones that need changing.
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
