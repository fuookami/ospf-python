"""混沌：Ikeda 映射。

Chaotic: Ikeda map.

Ikeda 映射描述激光腔中的光场混沌行为 (Ikeda, 1979)。
Ikeda map describes chaotic light field behavior in
laser cavities (Ikeda, 1979).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class IkedaMap:
    """Ikeda 映射，二维离散动力系统。

    Ikeda map, a 2D discrete dynamical system.

    t = 0.4 - 6/(1 + x² + y²)
    x_{n+1} = 1 + u*(x*cos(t) - y*sin(t))
    y_{n+1} = u*(x*sin(t) + y*cos(t))

    Attributes:
        u: 非线性强度参数。/ Nonlinearity strength.
    """

    u: float = 0.9

    def __call__(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 值。/ Current x value.
            y: 当前 y 值。/ Current y value.

        Returns:
            下一步的 (x, y)。/ Next (x, y).
        """
        t = 0.4 - 6.0 / (1.0 + x * x + y * y)
        cos_t = math.cos(t)
        sin_t = math.sin(t)
        return (
            1.0 + self.u * (x * cos_t - y * sin_t),
            self.u * (x * sin_t + y * cos_t),
        )

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
            x: 初始 x 值。/ Initial x value.
            y: 初始 y 值。/ Initial y value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y)。/ (x, y) after n steps.
        """
        cx, cy = x, y
        for _ in range(n):
            cx, cy = self(cx, cy)
        return cx, cy
