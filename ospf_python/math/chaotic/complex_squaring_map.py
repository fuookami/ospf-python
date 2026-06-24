"""混沌：复数平方映射。

Chaotic: Complex squaring map.

复数平方映射 z → z² + c，是 Mandelbrot 集的基础迭代。
Complex squaring map z -> z² + c, the basis of Mandelbrot set iteration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplexSquaringMap:
    """复数平方映射，一维复域迭代。

    Complex squaring map, a 1D complex-valued iteration.

    z_{n+1} = z_n² + c

    Attributes:
        c: 复常数 c。/ Complex constant c.
    """

    c: complex = complex(-0.7, 0.27015)

    def __call__(self, z: complex) -> complex:
        """执行单步迭代。

        Perform a single iteration.

        Args:
            z: 当前复数值。/ Current complex value.

        Returns:
            下一步的复数值。/ Next complex value.
        """
        return z * z + self.c

    def iterate(
        self,
        z: complex,
        *,
        n: int,
    ) -> complex:
        """执行 n 步迭代。

        Perform n iterations.

        Args:
            z: 初始复数值。/ Initial complex value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的复数值。/ Complex value after n steps.
        """
        cz = z
        for _ in range(n):
            cz = self(cz)
        return cz
