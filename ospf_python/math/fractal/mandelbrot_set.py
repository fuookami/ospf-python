"""分形：Mandelbrot 集。

Fractal: Mandelbrot set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MandelbrotSet:
    """Mandelbrot 集合，用于判断复平面上的点是否属于 Mandelbrot 集。

    Mandelbrot set for determining membership of points
    in the complex plane.

    Attributes:
        max_iter: 默认最大迭代次数。/ Default max iterations.
    """

    max_iter: int = 100

    @staticmethod
    def iterate(c: complex, max_iter: int) -> int:
        """从 z=0 开始迭代 z -> z^2 + c，返回逃逸时的迭代次数。

        Iterate z -> z^2 + c starting from z=0, returning
        the iteration count at escape.

        如果在 max_iter 次迭代内未逃逸，返回 max_iter。
        If it does not escape within max_iter iterations,
        returns max_iter.

        Args:
            c: 复数参数。/ Complex parameter.
            max_iter: 最大迭代次数。/ Maximum iterations.

        Returns:
            逃逸迭代次数或 max_iter。
            Escape iteration count or max_iter.
        """
        z = complex(0.0, 0.0)
        for i in range(max_iter):
            if z.real * z.real + z.imag * z.imag > 4.0:
                return i
            z = z * z + c
        return max_iter

    def contains(self, c: complex) -> bool:
        """判断复数 c 是否属于 Mandelbrot 集（不逃逸）。

        Determine if complex c belongs to the Mandelbrot set
        (does not escape).

        Args:
            c: 待判断的复数。/ Complex number to check.

        Returns:
            是否属于 Mandelbrot 集。/ Whether in the set.
        """
        iters = MandelbrotSet.iterate(c, self.max_iter)
        return iters == self.max_iter
