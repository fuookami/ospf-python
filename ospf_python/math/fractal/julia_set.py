"""分形：Julia 集。

Fractal: Julia set.
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
        z: SupportsComplex,
        c: SupportsComplex,
        max_iter: SupportsIndex,
    ) -> BindingResult[int]:
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
        if (
            type(z) is complex
            and type(c) is complex
            and (type(max_iter) is int or type(max_iter) is bool)
        ):
            count = max_iter
            if count > _fractal._U64_MAX:
                return _fractal._resource_failure()
            if count <= 0:
                return Ok(count)
            value, transport_error = _native._fractal_escape_time(z, c, count)
            if transport_error is None:
                if value is None:
                    return invalid(
                        "原生分形结果缺失 / Native fractal result is missing"
                    )
                return Ok(value)
            return _fractal._transport_failure(transport_error)
        return _fractal.julia_iterate(z, c, max_iter)

    def contains(self, x: float, y: float) -> BindingResult[bool]:
        """判断点 (x, y) 是否属于 Julia 集（不逃逸）。

        Determine if point (x, y) belongs to the Julia set
        (does not escape).

        Args:
            x: 实部坐标。/ Real coordinate.
            y: 虚部坐标。/ Imaginary coordinate.

        Returns:
            是否属于 Julia 集。/ Whether in the Julia set.
        """
        if (
            type(x) is float
            and type(y) is float
            and type(self.c_real) is float
            and type(self.c_imag) is float
        ):
            parameter = complex(self.c_real, self.c_imag)
            current = complex(x, y)
            return JuliaSet.iterate(current, parameter, self.max_iter).map(
                lambda iterations: iterations == self.max_iter
            )
        values = _fractal.julia_contains_pair(
            x=x,
            y=y,
            c_real=self.c_real,
            c_imag=self.c_imag,
            max_iterations=self.max_iter,
        )
        return values.flat_map(
            lambda pair: JuliaSet.iterate(pair[0], pair[1], self.max_iter)
        ).map(lambda iterations: iterations == self.max_iter)
