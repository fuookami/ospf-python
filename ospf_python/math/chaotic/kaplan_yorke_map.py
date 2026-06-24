"""混沌映射：Kaplan-Yorke 映射。

Chaotic map: Kaplan-Yorke map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class KaplanYorkeMap:
    """Kaplan-Yorke 映射，一个二维分段线性混沌映射。

    Kaplan-Yorke map, a 2D piecewise-linear chaotic map.

    映射规则：
    x_{n+1} = 2 * x_n  (mod 1)
    y_{n+1} = alpha * y_n + cos(4 * pi * x_n)  (mod 1)

    Map rules:
    x_{n+1} = 2 * x_n  (mod 1)
    y_{n+1} = alpha * y_n + cos(4 * pi * x_n)  (mod 1)

    Attributes:
        alpha: 收缩参数。/ Contraction parameter.
    """

    alpha: float = 0.2

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
        x_new = (2.0 * x) % 1.0
        y_new = (self.alpha * y + math.cos(4.0 * math.pi * x)) % 1.0
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
