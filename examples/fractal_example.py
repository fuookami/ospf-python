"""固定 Rust 分形迭代示例。 / Pinned-Rust fractal iteration example."""

from __future__ import annotations

from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet


def main() -> None:
    """演示两个公开分形类显式消费 Result。 / Demonstrate explicit Result consumption for both public fractal classes."""
    mandelbrot = MandelbrotSet(max_iter=200).contains(complex(-0.5, 0.0)).unwrap()
    julia = JuliaSet(max_iter=500).contains(0.1, 0.1).unwrap()
    assert mandelbrot is True
    assert julia is True


if __name__ == "__main__":
    main()
