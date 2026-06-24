"""混沌：姜饼人映射。

Chaotic: Gingerbreadman map.

姜饼人映射因迭代轨迹形似姜饼人而得名。
Gingerbreadman map is named after the gingerbread man
shape of its iterative trajectory.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GingerbreadmanMap:
    """姜饼人映射，二维离散动力系统。

    Gingerbreadman map, a 2D discrete dynamical system.

    x_{n+1} = 1 - y_n + |x_n|
    y_{n+1} = x_n
    """

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
        return (1.0 - y + abs(x), x)

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
