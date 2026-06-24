"""分形：Julia 集。

Fractal: Julia set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JuliaSet:
    """Julia 集合，用于判断复平面上的点是否属于 Julia 集。

    Julia set for determining membership of points
    in the complex plane.

    Attributes:
        c_real: 参数 c 的实部。/ Real part of parameter c.
        c_imag: 参数 c 的虚部。/ Imaginary part of parameter c.
        max_iter: 默认最大迭代次数。/ Default max iterations.
        escape_radius: 逃逸半径。/ Escape radius.
    """

    c_real: float = -0.7
    c_imag: float = 0.27015
    max_iter: int = 100
    escape_radius: float = 2.0

    @staticmethod
    def iterate(
        z: complex,
        c: complex,
        max_iter: int,
    ) -> int:
        """对 z 应用迭代 z -> z^2 + c，返回逃逸时的迭代次数。

        Apply iteration z -> z^2 + c, returning the iteration
        count at escape.

        如果在 max_iter 次迭代内未逃逸，返回 max_iter。
        If it does not escape within max_iter iterations,
        returns max_iter.

        Args:
            z: 初始复数值。/ Initial complex value.
            c: 迭代参数。/ Iteration parameter.
            max_iter: 最大迭代次数。/ Maximum iterations.

        Returns:
            逃逸迭代次数或 max_iter。
            Escape iteration count or max_iter.
        """
        current = z
        for i in range(max_iter):
            if current.real * current.real + current.imag * current.imag > 4.0:
                return i
            current = current * current + c
        return max_iter

    def contains(self, x: float, y: float) -> bool:
        """判断点 (x, y) 是否属于 Julia 集（不逃逸）。

        Determine if point (x, y) belongs to the Julia set
        (does not escape).

        Args:
            x: 实部坐标。/ Real coordinate.
            y: 虚部坐标。/ Imaginary coordinate.

        Returns:
            是否属于 Julia 集。/ Whether in the Julia set.
        """
        c = complex(self.c_real, self.c_imag)
        z = complex(x, y)
        iters = JuliaSet.iterate(z, c, self.max_iter)
        return iters == self.max_iter
