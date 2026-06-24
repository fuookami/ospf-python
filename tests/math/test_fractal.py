"""分形模块测试。

Fractal module tests.

测试 Julia 集和 Mandelbrot 集的成员判定。
Tests Julia set and Mandelbrot set membership.
"""

from __future__ import annotations

from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet

# ── JuliaSet ─────────────────────────────────────────────────────


class TestJuliaSet:
    """Julia 集测试。"""

    def test_interior_point_in_set(self) -> None:
        """内部点在 Julia 集中。/ Interior point in Julia set."""
        js = JuliaSet(c_real=-0.7, c_imag=0.27015, max_iter=500)
        assert js.contains(0.1, 0.1)

    def test_far_point_escapes(self) -> None:
        """远离原点的点逃逸。/ Far point escapes."""
        js = JuliaSet(c_real=-0.7, c_imag=0.27015, max_iter=100)
        assert not js.contains(10.0, 10.0)

    def test_iterate_returns_early(self) -> None:
        """快速逃逸的迭代次数少。/ Fast escape returns low count."""
        c = complex(-0.7, 0.27015)
        z = complex(100.0, 100.0)
        iters = JuliaSet.iterate(z, c, 100)
        assert iters < 10

    def test_iterate_max(self) -> None:
        """不逃逸时返回 max_iter。/ Non-escape returns max_iter."""
        c = complex(-0.7, 0.27015)
        z = complex(0.1, 0.1)
        iters = JuliaSet.iterate(z, c, 200)
        assert iters == 200

    def test_default_params(self) -> None:
        """默认参数创建。/ Default parameter creation."""
        js = JuliaSet()
        assert js.c_real == -0.7
        assert js.c_imag == 0.27015
        assert js.max_iter == 100

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        js = JuliaSet(max_iter=50)
        assert js.max_iter == 50


# ── MandelbrotSet ────────────────────────────────────────────────


class TestMandelbrotSet:
    """Mandelbrot 集测试。"""

    def test_origin_in_set(self) -> None:
        """原点在 Mandelbrot 集中。/ Origin is in Mandelbrot set."""
        ms = MandelbrotSet(max_iter=100)
        assert ms.contains(complex(0.0, 0.0))

    def test_one_in_set(self) -> None:
        """c=-1 在 Mandelbrot 集中。/ c=-1 is in Mandelbrot set."""
        ms = MandelbrotSet(max_iter=100)
        assert ms.contains(complex(-1.0, 0.0))

    def test_two_escapes(self) -> None:
        """c=2 逃逸。/ c=2 escapes."""
        ms = MandelbrotSet(max_iter=100)
        assert not ms.contains(complex(2.0, 0.0))

    def test_complex_escapes(self) -> None:
        """c=1+i 逃逸。/ c=1+i escapes."""
        ms = MandelbrotSet(max_iter=100)
        assert not ms.contains(complex(1.0, 1.0))

    def test_iterate_origin(self) -> None:
        """原点迭代不逃逸。/ Origin iteration does not escape."""
        iters = MandelbrotSet.iterate(complex(0.0, 0.0), 100)
        assert iters == 100

    def test_iterate_escapes_fast(self) -> None:
        """大参数快速逃逸。/ Large parameter escapes fast."""
        iters = MandelbrotSet.iterate(complex(100.0, 100.0), 100)
        assert iters < 5

    def test_default_max_iter(self) -> None:
        """默认最大迭代次数。/ Default max iterations."""
        ms = MandelbrotSet()
        assert ms.max_iter == 100

    def test_custom_max_iter(self) -> None:
        """自定义最大迭代次数。/ Custom max iterations."""
        ms = MandelbrotSet(max_iter=50)
        assert ms.max_iter == 50

    def test_cardioid_point(self) -> None:
        """心形线内点。/ Cardioid interior point."""
        ms = MandelbrotSet(max_iter=100)
        assert ms.contains(complex(-0.5, 0.0))

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        ms = MandelbrotSet(max_iter=200)
        assert ms.max_iter == 200
