"""混沌映射：区间交换变换。

Chaotic map: Interval exchange transformation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntervalExchangeTransformation:
    """区间交换变换，将 [0, 1) 上的多个子区间按置换重新排列。

    Interval exchange transformation that permutes
    sub-intervals on [0, 1).

    Attributes:
        endpoints: 区间端点，升序排列。
            Interval endpoints in ascending order.
        permutation: 区间索引的置换。
            Permutation of interval indices.
    """

    endpoints: tuple[float, ...] = (0.0, 0.5, 1.0)
    permutation: tuple[int, ...] = (1, 0)

    def __call__(self, x: float) -> float:
        """对单个点执行一次变换。

        Apply one step of the transformation.

        Args:
            x: 当前状态值。/ Current state value.

        Returns:
            变换后的值。/ Transformed value.
        """
        eps = self.endpoints
        perm = self.permutation
        n = len(perm)
        for i in range(n):
            if eps[i] <= x < eps[i + 1]:
                return eps[perm[i]] + x - eps[i]
        return x

    def iterate(
        self,
        x: float,
        *,
        n: int = 100,
    ) -> float:
        """迭代变换 n 次。

        Iterate the transformation n times.

        Args:
            x: 初始状态值。/ Initial state value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终状态值。/ Final state value.
        """
        result = x
        for _ in range(n):
            result = self(result)
        return result
