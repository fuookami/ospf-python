"""混沌：Zaslavskii 映射。

Chaotic: Zaslavskii map.

Zaslavskii 映射是一种二维离散混沌系统，
用于描述粒子在波场中的运动。
Zaslavskii map is a 2D discrete chaotic system
describing particle motion in a wave field.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ZaslavskiiMap:
    """Zaslavskii 映射，二维离散混沌系统。

    Zaslavskii map, a 2D discrete chaotic system.

    x_{n+1} = (x_n + epsilon * (1 + mu * y_n) + r * mu * cos(2pi * x_n)) mod 1
    y_{n+1} = exp(-r) * (y_n + epsilon * cos(2pi * x_n))

    Attributes:
        epsilon: 非线性参数 epsilon。/ Nonlinearity parameter epsilon.
        mu: 阻尼参数 mu。/ Damping parameter mu.
        r: 耗散参数 r。/ Dissipation parameter r.
    """

    epsilon: float = 4.9
    mu: float = 0.01
    r: float = 3.0

    def __call__(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 坐标。/ Current x coordinate.
            y: 当前 y 坐标。/ Current y coordinate.

        Returns:
            下一步的 (x, y)。/ Next (x, y).
        """
        phase = 2 * math.pi * x
        x_new = (
            x + self.epsilon * (1 + self.mu * y) + self.r * self.mu * math.cos(phase)
        ) % 1
        y_new = math.exp(-self.r) * (y + self.epsilon * math.cos(phase))
        return x_new, y_new

    def iterate(
        self,
        x: float,
        y: float,
        *,
        n: int,
    ) -> tuple[float, float]:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            x: 初始 x 坐标。/ Initial x coordinate.
            y: 初始 y 坐标。/ Initial y coordinate.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y)。/ (x, y) after n steps.
        """
        cx, cy = x, y
        for _ in range(n):
            cx, cy = self(cx, cy)
        return cx, cy
