"""混沌：辛映射。

Chaotic: Symplectic map.

辛映射保持相空间面积，是一种保结构的混沌映射。
Symplectic map preserves phase-space area,
a structure-preserving chaotic map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SymplecticMap:
    """辛映射，二维保面积混沌系统。

    Symplectic map, a 2D area-preserving chaotic system.

    x_{n+1} = x_n + k * sin(y_n)
    y_{n+1} = y_n + x_{n+1}

    Attributes:
        k: 非线性参数。/ Nonlinearity parameter.
    """

    k: float = 0.971635

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
        x_new = x + self.k * math.sin(y)
        y_new = y + x_new
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
