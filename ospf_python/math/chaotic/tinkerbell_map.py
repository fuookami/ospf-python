"""混沌：Tinkerbell 映射。

Chaotic: Tinkerbell map.

Tinkerbell 映射是一种二维离散混沌系统。
Tinkerbell map is a 2D discrete chaotic system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TinkerbellMap:
    """Tinkerbell 映射，二维离散混沌系统。

    Tinkerbell map, a 2D discrete chaotic system.

    x_{n+1} = x_n^2 - y_n^2 + a * x_n + b * y_n
    y_{n+1} = 2 * x_n * y_n + c * x_n + d * y_n

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
        c: 控制参数 c。/ Control parameter c.
        d: 控制参数 d。/ Control parameter d.
    """

    a: float = 0.9
    b: float = -0.6013
    c: float = 2.0
    d: float = 0.5

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
        x_new = x * x - y * y + self.a * x + self.b * y
        y_new = 2 * x * y + self.c * x + self.d * y
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
