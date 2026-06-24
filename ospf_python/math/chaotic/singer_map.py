"""混沌：Singer 映射。

Chaotic: Singer map.

Singer 映射是一维参数化混沌映射。
Singer map is a 1D parametric chaotic map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SingerMap:
    """Singer 映射，一维离散混沌系统。

    Singer map, a 1D discrete chaotic system.

    x_{n+1} = mu * (a1 * x_n - a2 * x_n^2 - a3 * x_n^3)

    Attributes:
        mu: 分岔参数。/ Bifurcation parameter.
        a1: 线性系数。/ Linear coefficient.
        a2: 二次系数。/ Quadratic coefficient.
        a3: 三次系数。/ Cubic coefficient.
    """

    mu: float = 1.07
    a1: float = 1.5
    a2: float = 0.5
    a3: float = 0.0

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前状态值。/ Current state value.

        Returns:
            下一步的状态值。/ Next state value.
        """
        return self.mu * (self.a1 * x - self.a2 * x * x - self.a3 * x * x * x)

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
