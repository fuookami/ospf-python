"""分形：Mandelbrot 集。

Fractal: Mandelbrot set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, SupportsComplex, SupportsIndex

from ospf_python import _native
from ospf_python._binding import fractal as _fractal
from ospf_python._binding.result import invalid
from ospf_python.utils.functional.result import Ok

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult


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
    def iterate(
        c: SupportsComplex,
        max_iter: SupportsIndex,
    ) -> BindingResult[int]:
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
        if type(c) is complex and (type(max_iter) is int or type(max_iter) is bool):
            count = max_iter
            if count > _fractal._U64_MAX:
                return _fractal._resource_failure()
            if count <= 0:
                return Ok(count)
            value, transport_error = _native._fractal_escape_time(0j, c, count)
            if transport_error is None:
                if value is None:
                    return invalid(
                        "原生分形结果缺失 / Native fractal result is missing"
                    )
                return Ok(value)
            return _fractal._transport_failure(transport_error)
        return _fractal.mandelbrot_iterate(c, max_iter)

    def contains(self, c: SupportsComplex) -> BindingResult[bool]:
        """判断复数 c 是否属于 Mandelbrot 集（不逃逸）。

        Determine if complex c belongs to the Mandelbrot set
        (does not escape).

        Args:
            c: 待判断的复数。/ Complex number to check.

        Returns:
            是否属于 Mandelbrot 集。/ Whether in the set.
        """
        return MandelbrotSet.iterate(c, self.max_iter).map(
            lambda iterations: iterations == self.max_iter
        )
