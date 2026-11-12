"""公开分形完整调用正确性，不冒充预算验收。 / Complete public fractal correctness, not budget acceptance."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet


@pytest.mark.parametrize(
    ("name", "operation", "expected"),
    [
        (
            "mandelbrot-origin",
            lambda: MandelbrotSet.iterate(complex(0.0, 0.0), 10_000).unwrap(),
            10_000,
        ),
        (
            "mandelbrot-escape",
            lambda: MandelbrotSet.iterate(complex(10.0, 10.0), 10_000).unwrap(),
            1,
        ),
        (
            "julia-interior",
            lambda: JuliaSet.iterate(
                complex(0.1, 0.1), complex(-0.7, 0.27015), 10_000
            ).unwrap(),
            684,
        ),
        (
            "julia-escape",
            lambda: JuliaSet.iterate(
                complex(100.0, 100.0), complex(-0.7, 0.27015), 10_000
            ).unwrap(),
            0,
        ),
    ],
    ids=["mandelbrot-origin", "mandelbrot-escape", "julia-interior", "julia-escape"],
)
def test_public_fractal_complete_call(
    *,
    benchmark: Any,
    name: str,
    operation: Callable[[], int],
    expected: int,
) -> None:
    del name
    assert benchmark(operation) == expected
