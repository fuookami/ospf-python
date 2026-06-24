"""Baker 映射。

Baker's map (2D piecewise-linear chaotic map).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BakersMap:
    """Baker 映射，二维分段线性混沌映射。

    Baker's map, a 2D piecewise-linear chaotic map
    on the unit square.

    经典形式: 将正方形拉伸为 2x(1/2) 矩阵，再折叠回正方形。

    Attributes:
        stretch: 拉伸因子。/ Stretch factor.
    """

    stretch: float = 2.0

    def __call__(self, x: float) -> float:
        """执行单步映射。

        Perform a single map step.

        Args:
            x: 当前值（一维投影）。/ Current value (1D projection).

        Returns:
            映射后的值。/ Mapped value.
        """
        if x < 0.5:
            return self.stretch * x
        return self.stretch * x - 1.0

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步。

        Iterate the map n times.

        Args:
            x: 初始值。/ Initial value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间值的列表。/ List of all intermediate values.
        """
        result = [x]
        current = x
        for _ in range(n):
            current = self(current)
            result.append(current)
        return result
