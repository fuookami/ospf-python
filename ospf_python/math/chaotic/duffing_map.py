"""混沌：Duffing 映射。

Chaotic: Duffing map.

Duffing 映射是 Duffing 方程的离散化版本。
Duffing map is a discretized version of the Duffing equation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DuffingMap:
    """Duffing 映射，二维离散动力系统。

    Duffing map, a 2D discrete dynamical system.

    x_{n+1} = y_n
    y_{n+1} = -b*x_n + a*y_n - y_n³

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
    """

    a: float = 2.75
    b: float = 0.2

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
        return (
            y,
            -self.b * x + self.a * y - y * y * y,
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
