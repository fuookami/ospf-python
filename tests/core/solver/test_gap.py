"""Gap 测试。

测试求解间隙的创建、工厂方法和容差检查。
Tests Gap creation, factory methods, and tolerance checks.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.gap import Gap


class TestGapDefaults:
    """默认值测试 / Default value tests."""

    def test_default_absolute(self) -> None:
        """默认绝对间隙为无穷。/ Default absolute is inf."""
        g = Gap()
        assert g.absolute == float("inf")

    def test_default_relative(self) -> None:
        """默认相对间隙为无穷。/ Default relative is inf."""
        g = Gap()
        assert g.relative == float("inf")


class TestGapFactories:
    """工厂方法测试 / Factory method tests."""

    def test_zero_factory(self) -> None:
        """零间隙工厂方法。/ Zero gap factory."""
        g = Gap.zero()
        assert g.absolute == 0.0
        assert g.relative == 0.0

    def test_infinity_factory(self) -> None:
        """无穷大间隙工厂方法。/ Infinity gap factory."""
        g = Gap.infinity()
        assert g.absolute == float("inf")
        assert g.relative == float("inf")


class TestGapTolerance:
    """容差检查测试 / Tolerance tests."""

    def test_within_tolerance(self) -> None:
        """在容差内。/ Within tolerance."""
        g = Gap(absolute=0.01, relative=0.001)
        assert g.is_within_tolerance(0.01) is True

    def test_not_within_tolerance(self) -> None:
        """不在容差内。/ Not within tolerance."""
        g = Gap(absolute=0.01, relative=0.1)
        assert g.is_within_tolerance(0.01) is False

    def test_exact_tolerance(self) -> None:
        """恰好等于容差。/ Exactly at tolerance."""
        g = Gap(absolute=0.01, relative=0.01)
        assert g.is_within_tolerance(0.01) is True


class TestGapFrozen:
    """不可变性测试 / Immutability tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        g = Gap()
        with pytest.raises(AttributeError):
            g.absolute = 0.0  # type: ignore[misc]
