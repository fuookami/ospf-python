"""VariableRange 测试。

测试变量范围的创建、边界检查和工厂方法。
Tests VariableRange creation, boundary checks,
and factory methods.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable.variable_range import VariableRange


class TestVariableRangeCreation:
    """创建测试 / Creation tests."""

    def test_create_default_range(self) -> None:
        """默认范围为 (-inf, inf)。/ Default is (-inf, inf)."""
        r = VariableRange()
        assert r.lower == float("-inf")
        assert r.upper == float("inf")

    def test_create_bounded_range(self) -> None:
        """创建有界范围。/ Create bounded range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.lower == 0.0
        assert r.upper == 10.0

    def test_is_frozen(self) -> None:
        """范围不可变。/ Range is frozen."""
        r = VariableRange(lower=0.0, upper=1.0)
        with pytest.raises(AttributeError):
            r.lower = 2.0  # type: ignore[misc]

    def test_equality(self) -> None:
        """范围相等性。/ Range equality."""
        r1 = VariableRange(lower=0.0, upper=1.0)
        r2 = VariableRange(lower=0.0, upper=1.0)
        assert r1 == r2


class TestVariableRangeContains:
    """包含检查测试 / Contains tests."""

    def test_contains_value_in_range(self) -> None:
        """包含范围内的值。/ Contains value in range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(5.0) is True

    def test_contains_boundary_value(self) -> None:
        """包含边界值。/ Contains boundary value."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(0.0) is True
        assert r.contains(10.0) is True

    def test_not_contains_out_of_range(self) -> None:
        """不包含范围外的值。/ Does not contain out-of-range."""
        r = VariableRange(lower=0.0, upper=10.0)
        assert r.contains(-1.0) is False
        assert r.contains(11.0) is False


class TestVariableRangeProperties:
    """属性测试 / Property tests."""

    def test_width(self) -> None:
        """范围宽度正确。/ Range width is correct."""
        r = VariableRange(lower=2.0, upper=8.0)
        assert r.width == 6.0

    def test_is_unbounded(self) -> None:
        """无界范围判断。/ Unbounded range detection."""
        r = VariableRange()
        assert r.is_unbounded() is True

    def test_is_not_unbounded(self) -> None:
        """有界范围非无界。/ Bounded range is not unbounded."""
        r = VariableRange(lower=0.0, upper=1.0)
        assert r.is_unbounded() is False


class TestVariableRangeFactories:
    """工厂方法测试 / Factory method tests."""

    def test_non_negative_factory(self) -> None:
        """非负范围工厂方法。/ Non-negative factory."""
        r = VariableRange.non_negative()
        assert r.lower == 0.0
        assert r.upper == float("inf")

    def test_unit_factory(self) -> None:
        """单位范围工厂方法。/ Unit range factory."""
        r = VariableRange.unit()
        assert r.lower == 0.0
        assert r.upper == 1.0

    def test_fixed_factory(self) -> None:
        """固定值范围工厂方法。/ Fixed value factory."""
        r = VariableRange.fixed(42.0)
        assert r.lower == 42.0
        assert r.upper == 42.0
        assert r.width == 0.0

    def test_create_factory(self) -> None:
        """create 工厂方法。/ create factory method."""
        r = VariableRange.create(lower=1.0, upper=5.0)
        assert r.lower == 1.0
        assert r.upper == 5.0
