"""复二次多项式。

Complex quadratic polynomial (Mandelbrot/Julia set iteration).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplexQuadraticPolynomial:
    """复二次多项式迭代，Mandelbrot/Julia 集的基础。

    Complex quadratic polynomial iteration, the basis
    for Mandelbrot and Julia sets.

    z_{n+1} = z_n^2 + c

    Attributes:
        c: 复参数 c 的实部。/ Real part of complex parameter c.
        ci: 复参数 c 的虚部。/ Imaginary part of complex parameter c.
    """

    c: float = -0.7
    ci: float = 0.27015

    def __call__(self, x: float) -> float:
        """执行单步映射（仅实部迭代）。

        Perform a single map step (real part iteration).

        此方法仅跟踪实部，适用于简化的一维分析。
        For full complex iteration, use iterate_complex.

        Args:
            x: 当前实部值。/ Current real value.

        Returns:
            下一步实部值。/ Next real value.
        """
        return x * x - x + self.c

    def iterate(self, x: float, *, n: int) -> list[float]:
        """迭代 n 步（仅实部）。

        Iterate n times (real part only).

        Args:
            x: 初始实部值。/ Initial real value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间值的列表。/ List of all intermediate values.
        """
        result = [x]
        current = x
        for _ in range(n):
            current = self(current)
            result.append(current)
        return result

    def iterate_complex(
        self, zr: float, zi: float, *, n: int
    ) -> list[tuple[float, float]]:
        """复数迭代 n 步。

        Complex iteration for n steps.

        z_{n+1} = z_n^2 + c，其中 z 和 c 为复数。

        Args:
            zr: 初始实部。/ Initial real part.
            zi: 初始虚部。/ Initial imaginary part.
            n: 迭代次数。/ Number of iterations.

        Returns:
            包含所有中间 (实部, 虚部) 的列表。
            List of all intermediate (real, imaginary) pairs.
        """
        result = [(zr, zi)]
        cr, ci_ = self.c, self.ci
        zr_cur, zi_cur = zr, zi
        for _ in range(n):
            new_r = zr_cur * zr_cur - zi_cur * zi_cur + cr
            new_i = 2.0 * zr_cur * zi_cur + ci_
            zr_cur, zi_cur = new_r, new_i
            result.append((zr_cur, zi_cur))
        return result
