"""Tests for ospf_python.math.ordinary module."""

from ospf_python.math.algebra.number import Float64
from ospf_python.math.ordinary import (
    clamp,
    gcd,
    is_prime,
    lcm,
    lerp,
    primes_up_to,
    sign,
    smoothstep,
)


class TestClamp:
    """Tests for clamp."""

    def test_clamp_in_range(self) -> None:
        """Test clamp when value is in range."""
        assert clamp(Float64(5.0), Float64(0.0), Float64(10.0)) == Float64(5.0)

    def test_clamp_below(self) -> None:
        """Test clamp when value is below range."""
        assert clamp(Float64(-5.0), Float64(0.0), Float64(10.0)) == Float64(0.0)

    def test_clamp_above(self) -> None:
        """Test clamp when value is above range."""
        assert clamp(Float64(15.0), Float64(0.0), Float64(10.0)) == Float64(10.0)


class TestLerp:
    """Tests for lerp."""

    def test_lerp_start(self) -> None:
        """Test lerp at t=0."""
        result = lerp(Float64(0.0), Float64(10.0), 0.0)
        assert result.to_float() == 0.0

    def test_lerp_end(self) -> None:
        """Test lerp at t=1."""
        result = lerp(Float64(0.0), Float64(10.0), 1.0)
        assert result.to_float() == 10.0

    def test_lerp_mid(self) -> None:
        """Test lerp at t=0.5."""
        result = lerp(Float64(0.0), Float64(10.0), 0.5)
        assert result.to_float() == 5.0


class TestSmoothstep:
    """Tests for smoothstep."""

    def test_smoothstep_edges(self) -> None:
        """Test smoothstep at edges."""
        assert smoothstep(0, 1, 0) == 0
        assert smoothstep(0, 1, 1) == 1

    def test_smoothstep_mid(self) -> None:
        """Test smoothstep at midpoint."""
        assert smoothstep(0, 1, 0.5) == 0.5


class TestSign:
    """Tests for sign."""

    def test_sign_positive(self) -> None:
        """Test sign of positive."""
        assert sign(Float64(5.0)) == 1

    def test_sign_negative(self) -> None:
        """Test sign of negative."""
        assert sign(Float64(-5.0)) == -1

    def test_sign_zero(self) -> None:
        """Test sign of zero."""
        assert sign(Float64(0.0)) == 0


class TestGcd:
    """Tests for gcd."""

    def test_gcd_basic(self) -> None:
        """Test basic gcd."""
        assert gcd(12, 8) == 4
        assert gcd(7, 13) == 1


class TestLcm:
    """Tests for lcm."""

    def test_lcm_basic(self) -> None:
        """Test basic lcm."""
        assert lcm(4, 6) == 12
        assert lcm(3, 7) == 21


class TestIsPrime:
    """Tests for is_prime."""

    def test_primes(self) -> None:
        """Test prime numbers."""
        assert is_prime(2)
        assert is_prime(3)
        assert is_prime(5)
        assert is_prime(7)
        assert is_prime(11)

    def test_non_primes(self) -> None:
        """Test non-prime numbers."""
        assert not is_prime(0)
        assert not is_prime(1)
        assert not is_prime(4)
        assert not is_prime(9)


class TestPrimesUpTo:
    """Tests for primes_up_to."""

    def test_primes_basic(self) -> None:
        """Test primes up to 10."""
        assert primes_up_to(10) == [2, 3, 5, 7]

    def test_primes_empty(self) -> None:
        """Test primes up to 1."""
        assert primes_up_to(1) == []
