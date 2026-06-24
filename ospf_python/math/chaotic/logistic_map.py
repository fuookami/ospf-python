"""混沌映射：Logistic 映射。

Chaotic map: Logistic map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogisticMap:
    """经典 Logistic 映射 x_{n+1} = r * x_n * (1 - x_n)。

    Classic logistic map x_{n+1} = r * x_n * (1 - x_n).

    当 r 在 [3.57, 4.0] 范围内时系统表现出混沌行为。
    The system exhibits chaotic behavior for
    r in [3.57, 4.0].

    Attributes:
        r: 增长率参数，通常在 [0, 4] 范围内。
            Growth rate parameter, typically in [0, 4].
    """

    r: float = 3.9

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Apply one iteration step.

        Args:
            x: 当前状态值，应在 [0, 1] 内。
                Current state value in [0, 1].

        Returns:
            下一步状态值。/ Next state value.
        """
        return self.r * x * (1.0 - x)

    def iterate(
        self,
        x: float,
        *,
        n: int = 100,
    ) -> float:
        """迭代映射 n 次。

        Iterate the map n times.

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
