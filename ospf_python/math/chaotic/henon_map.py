"""混沌：Hénon 映射。

Chaotic: Hénon map.

Hénon 映射是最经典的二维离散混沌映射之一 (Hénon, 1976)。
Hénon map is one of the most classical 2D discrete
chaotic maps (Hénon, 1976).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HenonMap:
    """Hénon 映射，二维离散动力系统。

    Hénon map, a 2D discrete dynamical system.

    x_{n+1} = 1 - a*x_n² + y_n
    y_{n+1} = b*x_n

    Attributes:
        a: 非线性参数。/ Nonlinearity parameter.
        b: 收缩参数。/ Contraction parameter.
    """

    a: float = 1.4
    b: float = 0.3

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
        x_new = 1.0 - self.a * x * x + y
        y_new = self.b * x
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
