"""Arnold 猫映射。

Arnold's cat map (2D discrete map on torus).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ArnoldsCatMap:
    """Arnold 猫映射，二维环面离散映射。

    Arnold's cat map, a 2D chaotic map on the torus.

    对单位正方形上的点 (x, y) 进行变换:
    (x', y') = (x + y mod 1, x + 2y mod 1).

    Attributes:
        a: 矩阵参数 a。/ Matrix parameter a.
        b: 矩阵参数 b。/ Matrix parameter b.
        c: 矩阵参数 c。/ Matrix parameter c.
        d: 矩阵参数 d。/ Matrix parameter d.
    """

    a: float = 1.0
    b: float = 1.0
    c: float = 1.0
    d: float = 2.0

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """执行单步映射。

        Perform a single map step.

        Args:
            x: 当前坐标 [x, y]。/ Current coordinates [x, y].

        Returns:
            映射后的坐标（取模 1）。/ Mapped coordinates (mod 1).
        """
        matrix = np.array([[self.a, self.b], [self.c, self.d]])
        result = matrix @ x
        return result % 1.0

    def iterate(
        self,
        x: NDArray[np.float64],
        *,
        n: int,
    ) -> list[NDArray[np.float64]]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始坐标。/ Initial coordinates.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间状态的列表。/ List of all intermediate states.
        """
        result = [x.copy()]
        current = x.copy()
        for _ in range(n):
            current = self(current)
            result.append(current.copy())
        return result
