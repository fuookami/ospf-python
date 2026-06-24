"""混沌映射：Lozi 映射。

Chaotic map: Lozi map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoziMap:
    """Lozi 映射，一个二维分段线性混沌映射。

    Lozi map, a 2D piecewise-linear chaotic map.

    映射规则：
    x_{n+1} = 1 - a * |x_n| + b * y_n
    y_{n+1} = x_n

    Map rules:
    x_{n+1} = 1 - a * |x_n| + b * y_n
    y_{n+1} = x_n

    Attributes:
        a: 非线性参数。/ Nonlinearity parameter.
        b: 线性耦合参数。
            Linear coupling parameter.
    """

    a: float = 1.7
    b: float = 0.5

    def __call__(
        self,
        state: tuple[float, float],
    ) -> tuple[float, float]:
        """执行单步迭代。

        Apply one iteration step.

        Args:
            state: 当前 (x, y) 状态。
                Current (x, y) state.

        Returns:
            下一步 (x, y) 状态。
            Next (x, y) state.
        """
        x, y = state
        x_new = 1.0 - self.a * abs(x) + self.b * y
        y_new = x
        return (x_new, y_new)

    def iterate(
        self,
        state: tuple[float, float],
        *,
        n: int = 100,
    ) -> tuple[float, float]:
        """迭代映射 n 次。

        Iterate the map n times.

        Args:
            state: 初始 (x, y) 状态。
                Initial (x, y) state.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终 (x, y) 状态。
            Final (x, y) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
