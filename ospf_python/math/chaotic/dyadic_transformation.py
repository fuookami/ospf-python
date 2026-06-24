"""混沌：二进变换（Bernoulli 映射）。

Chaotic: Dyadic transformation (Bernoulli map).

二进变换 x → 2x mod 1 是最简单的一维混沌映射之一。
Dyadic transformation x -> 2x mod 1 is one of the
simplest 1D chaotic maps.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DyadicTransformation:
    """二进变换，一维离散混沌映射。

    Dyadic transformation, a 1D discrete chaotic map.

    x_{n+1} = 2 * x_n mod 1

    该映射等价于 Bernoulli 移位映射。
    This map is equivalent to the Bernoulli shift map.
    """

    def __call__(self, x: float) -> float:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            x: 当前 x 值（应在 [0, 1) 范围内）。
               Current x value (should be in [0, 1)).

        Returns:
            下一步的 x 值。/ Next x value.
        """
        return (2.0 * x) % 1.0

    def iterate(
        self,
        x: float,
        *,
        n: int,
    ) -> float:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            x: 初始 x 值。/ Initial x value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 x 值。/ x value after n steps.
        """
        cx = x
        for _ in range(n):
            cx = self(cx)
        return cx
