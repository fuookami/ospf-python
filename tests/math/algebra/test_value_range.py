"""Tests for ospf_python.math.algebra.value_range module."""

from ospf_python.math.algebra.number import Float64
from ospf_python.math.algebra.value_range import (
    ClosedTypedValueRange,
    TypedValueRange,
    create_closed_range,
    create_range,
)


class TestTypedValueRange:
    """Tests for TypedValueRange."""

    def test_creation(self) -> None:
        """Test creating range."""
        r = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r.lower is not None
        assert r.upper is not None

    def test_contains(self) -> None:
        """Test contains."""
        r = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r.contains(Float64(5.0))
        assert not r.contains(Float64(15.0))
        assert not r.contains(Float64(-5.0))

    def test_contains_unbounded_lower(self) -> None:
        """Test contains with no lower bound."""
        r = TypedValueRange(lower=None, upper=Float64(10.0))
        assert r.contains(Float64(-100.0))
        assert not r.contains(Float64(15.0))

    def test_contains_unbounded_upper(self) -> None:
        """Test contains with no upper bound."""
        r = TypedValueRange(lower=Float64(0.0), upper=None)
        assert r.contains(Float64(100.0))
        assert not r.contains(Float64(-5.0))

    def test_is_bounded(self) -> None:
        """Test is_bounded."""
        r1 = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r1.is_bounded()

        r2 = TypedValueRange(lower=None, upper=Float64(10.0))
        assert not r2.is_bounded()

    def test_is_lower_bounded(self) -> None:
        """Test is_lower_bounded."""
        r1 = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r1.is_lower_bounded()

        r2 = TypedValueRange(lower=None, upper=Float64(10.0))
        assert not r2.is_lower_bounded()

    def test_is_upper_bounded(self) -> None:
        """Test is_upper_bounded."""
        r1 = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r1.is_upper_bounded()

        r2 = TypedValueRange(lower=Float64(0.0), upper=None)
        assert not r2.is_upper_bounded()

    def test_repr(self) -> None:
        """Test repr."""
        r = TypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert "TypedValueRange" in repr(r)


class TestClosedTypedValueRange:
    """Tests for ClosedTypedValueRange."""

    def test_creation(self) -> None:
        """Test creating closed range."""
        r = ClosedTypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r.lower is not None
        assert r.upper is not None

    def test_contains(self) -> None:
        """Test contains (inclusive)."""
        r = ClosedTypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert r.contains(Float64(0.0))
        assert r.contains(Float64(10.0))
        assert r.contains(Float64(5.0))
        assert not r.contains(Float64(15.0))

    def test_repr(self) -> None:
        """Test repr."""
        r = ClosedTypedValueRange(lower=Float64(0.0), upper=Float64(10.0))
        assert "ClosedTypedValueRange" in repr(r)


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_range(self) -> None:
        """Test create_range."""
        r = create_range(lower=Float64(0.0), upper=Float64(10.0))
        assert isinstance(r, TypedValueRange)

    def test_create_closed_range(self) -> None:
        """Test create_closed_range."""
        r = create_closed_range(lower=Float64(0.0), upper=Float64(10.0))
        assert isinstance(r, ClosedTypedValueRange)
