"""Tests for ospf_python.math.fractal module."""

import pytest

from ospf_python.math.fractal import (
    fractal_dimension_box,
    julia_iteration,
    mandelbrot_iteration,
)


class TestFractalDimension:
    """Tests for fractal dimension."""

    def test_dimension_basic(self) -> None:
        """Test basic dimension calculation."""
        # Sierpinski triangle: D = log(3) / log(2) ≈ 1.585
        d = fractal_dimension_box(3, 0.5)
        assert abs(d - 1.585) < 0.01

    def test_dimension_invalid_count_raises(self) -> None:
        """Test invalid count raises."""
        with pytest.raises(ValueError):
            fractal_dimension_box(0, 0.5)

    def test_dimension_invalid_scale_raises(self) -> None:
        """Test invalid scale raises."""
        with pytest.raises(ValueError):
            fractal_dimension_box(3, 1.0)


class TestMandelbrot:
    """Tests for Mandelbrot iteration."""

    def test_mandelbrot_in_set(self) -> None:
        """Test point in Mandelbrot set."""
        assert mandelbrot_iteration(0 + 0j, 100) == 100
        assert mandelbrot_iteration(-1 + 0j, 100) == 100

    def test_mandelbrot_escapes(self) -> None:
        """Test point escapes."""
        assert mandelbrot_iteration(2 + 2j, 100) < 100


class TestJulia:
    """Tests for Julia iteration."""

    def test_julia_in_set(self) -> None:
        """Test point in Julia set."""
        # c = -0.7 + 0.27j, z = 0 is in the set
        assert julia_iteration(0 + 0j, -0.7 + 0.27j, 100) == 100

    def test_julia_escapes(self) -> None:
        """Test point escapes."""
        assert julia_iteration(2 + 2j, -0.7 + 0.27j, 100) < 100
