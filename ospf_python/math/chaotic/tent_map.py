"""混沌：帐篷映射。

Chaotic: Tent map.

帐篷映射是一种分段线性的一维混沌映射。
Tent map is a piecewise-linear 1D chaotic map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TentMap:
    """帐篷映射，一维分段线性混沌系统。

    Tent map, a 1D piecewise-linear chaotic system.

    x_{n+1} = mu * min(x_n, 1 - x_n)

    Attributes:
        mu: 控制参数，通常在 (1, 2] 范围内。
            Control parameter, typically in (1, 2].
    """

    mu: float = 2.0

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前状态值，应在 [0, 1] 内。
                Current state value, should be in [0, 1].

        Returns:
            下一步的状态值。/ Next state value.
        """
        return self.mu * min(x, 1.0 - x)

    def iterate(self, x: float, *, n: int) -> float:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            x: 初始状态值。/ Initial state value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的状态值。/ State value after n steps.
        """
        cx = x
        for _ in range(n):
            cx = self(cx)
        return cx
