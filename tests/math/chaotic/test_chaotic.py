"""Tests for ospf_python.math.chaotic module."""

import math

from ospf_python.math.chaotic import (
    bifurcation_diagram,
    circle_map,
    gauss_map,
    henon_map,
    ikeda_map,
    logistic_map,
    lorenz_step,
    lyapunov_exponent,
    rossler_step,
    sine_map,
    standard_map,
    tent_map,
)


class TestLogisticMap:
    """Tests for logistic map."""

    def test_basic(self) -> None:
        """Test basic logistic map."""
        # r=2, x=0.5 -> 0.5
        assert logistic_map(0.5, 2.0) == 0.5

    def test_r4(self) -> None:
        """Test logistic map with r=4."""
        # r=4, x=0.1 -> 0.36
        result = logistic_map(0.1, 4.0)
        assert abs(result - 0.36) < 1e-10


class TestTentMap:
    """Tests for tent map."""

    def test_basic(self) -> None:
        """Test basic tent map."""
        assert abs(tent_map(0.3, 2.0) - 0.6) < 1e-10
        assert abs(tent_map(0.7, 2.0) - 0.6) < 1e-10


class TestSineMap:
    """Tests for sine map."""

    def test_basic(self) -> None:
        """Test basic sine map."""
        result = sine_map(0.5, 1.0)
        expected = math.sin(math.pi * 0.5)
        assert abs(result - expected) < 1e-10


class TestGaussMap:
    """Tests for Gauss map."""

    def test_zero(self) -> None:
        """Test Gauss map with zero."""
        assert gauss_map(0, 1.0) == 0

    def test_basic(self) -> None:
        """Test basic Gauss map."""
        result = gauss_map(1.0, 1.0)
        expected = math.exp(-1.0)
        assert abs(result - expected) < 1e-10


class TestCircleMap:
    """Tests for circle map."""

    def test_basic(self) -> None:
        """Test basic circle map."""
        result = circle_map(0.5, 0.1, 1.0)
        assert 0 <= result <= 1


class TestHenonMap:
    """Tests for Henon map."""

    def test_basic(self) -> None:
        """Test basic Henon map."""
        x, y = henon_map(0.1, 0.1)
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_custom_params(self) -> None:
        """Test Henon map with custom parameters."""
        x, y = henon_map(0.1, 0.1, a=1.0, b=0.5)
        assert isinstance(x, float)


class TestIkedaMap:
    """Tests for Ikeda map."""

    def test_basic(self) -> None:
        """Test basic Ikeda map."""
        x, y = ikeda_map(0.1, 0.1)
        assert isinstance(x, float)
        assert isinstance(y, float)


class TestStandardMap:
    """Tests for standard map."""

    def test_basic(self) -> None:
        """Test basic standard map."""
        theta, p = standard_map(0.1, 0.2)
        assert 0 <= theta <= 2 * math.pi
        assert 0 <= p <= 2 * math.pi


class TestLorenzStep:
    """Tests for Lorenz system step."""

    def test_basic(self) -> None:
        """Test basic Lorenz step."""
        x, y, z = lorenz_step(1.0, 1.0, 1.0)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)


class TestRosslerStep:
    """Tests for Rossler system step."""

    def test_basic(self) -> None:
        """Test basic Rossler step."""
        x, y, z = rossler_step(1.0, 1.0, 1.0)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)


class TestBifurcationDiagram:
    """Tests for bifurcation diagram."""

    def test_basic(self) -> None:
        """Test basic bifurcation diagram."""
        results = bifurcation_diagram(
            logistic_map,
            (2.0, 4.0),
            n_points=10,
            n_transient=50,
            n_iter=50,
        )
        assert len(results) == 10
        for r, values in results:
            assert 2.0 <= r <= 4.0
            assert len(values) == 50


class TestLyapunovExponent:
    """Tests for Lyapunov exponent."""

    def test_logistic_r2(self) -> None:
        """Test Lyapunov exponent for logistic map at r=2."""
        # At r=2, the fixed point is stable, so Lyapunov < 0
        le = lyapunov_exponent(logistic_map, 0.5, 2.0, n_iter=100)
        assert le < 0

    def test_logistic_r4(self) -> None:
        """Test Lyapunov exponent for logistic map at r=4."""
        # At r=4, the system is chaotic, so Lyapunov > 0
        le = lyapunov_exponent(logistic_map, 0.1, 4.0, n_iter=1000)
        assert le > 0
