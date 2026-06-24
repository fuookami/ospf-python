"""混沌映射：Newton 迭代法。

Chaotic map: Newton iteration method.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewtonIterate:
    """Newton 迭代法，用于求解多项式根的迭代方法。

    Newton iteration method for finding polynomial
    roots through iteration.

    对多项式 p(z) = z^power - 1 应用 Newton 方法：
    z_{n+1} = z_n - p(z_n) / p'(z_n)

    Applying Newton method to p(z) = z^power - 1:
    z_{n+1} = z_n - p(z_n) / p'(z_n)

    在复平面上产生分形结构。
    Produces fractal structure in the complex plane.

    Attributes:
        power: 多项式的幂次。/ Polynomial power.
        damping: 阻尼系数。/ Damping coefficient.
    """

    power: int = 3
    damping: float = 1.0

    def __call__(self, x: complex) -> complex:
        """执行单步 Newton 迭代。

        Apply one Newton iteration step.

        对 p(z) = z^power - 1 进行 Newton 迭代。
        Newton iteration for p(z) = z^power - 1.

        Args:
            x: 当前复数值。/ Current complex value.

        Returns:
            下一步复数值。/ Next complex value.
        """
        n = self.power
        zn = x**n
        # f(z) = z^n - 1, f'(z) = n * z^(n-1)
        denom = n * x ** (n - 1)
        if abs(denom) < 1e-15:
            return x
        return x - self.damping * (zn - 1.0) / denom

    def iterate(
        self,
        x: complex,
        *,
        n: int = 100,
    ) -> complex:
        """迭代 Newton 方法 n 次。

        Iterate Newton method n times.

        Args:
            x: 初始复数值。/ Initial complex value.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终复数值。/ Final complex value.
        """
        result = x
        for _ in range(n):
            result = self(result)
        return result
