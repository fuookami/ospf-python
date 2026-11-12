"""混沌：Wimol-Banlue 吸引子。

Chaotic: Wimol-Banlue attractor.

Wimol-Banlue 系统是一种三维混沌吸引子。
Wimol-Banlue system is a 3D chaotic attractor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class WimolBanlueAttractor:
    """Wimol-Banlue 吸引子，三维混沌系统。

    Wimol-Banlue attractor, a 3D chaotic system.

    dx/dt = y - x
    dy/dt = -z * tanh(x)
    dz/dt = -a + x * y + |y|

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        dt: 时间步长。/ Time step.
    """

    a: float = 0.1
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
        # 决定 5 / B311：**回到标准 Wimol-Banlue 式**。线上权威（TU Delft 论文，采用
        # `β→0` 让 `√(y²+β²)` 逼近 `|y|` 的写法）给出
        # `ẋ = y − x`、`ẏ = −z·tanh(x)`、`ż = −α + xy + √(y²+β²) → −α + xy + |y|`。
        # 出厂式缺了 `+|y|` 项；`ospf-kotlin` 与上游 Rust 用 `tan` 且用 `|x|`——两者都偏离。
        # Back to the STANDARD Wimol-Banlue form (B311). The TU Delft reference (using the
        # beta->0 limit of sqrt(y^2+beta^2) ~ |y|) gives dx=y-x, dy=-z*tanh(x),
        # dz=-alpha+x*y+|y|. The shipped form omitted +|y|; kotlin and Rust use tan and |x|.
        dx = y - x
        dy = -z * math.tanh(x)
        dz = -self.a + x * y + abs(y)
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
