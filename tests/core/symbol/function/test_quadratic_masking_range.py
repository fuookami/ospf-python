"""QuadraticMaskingRange 测试。

测试二次掩码范围函数符号的创建和求值。
Tests QuadraticMaskingRange function symbol creation
and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.quadratic_masking_range import (
    QuadraticMaskingRange,
)


class TestQuadraticMaskingRange:
    """二次掩码范围测试 / QuadraticMaskingRange tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = QuadraticMaskingRange()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = QuadraticMaskingRange()
        assert str(s) == "QuadraticMaskingRange"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = QuadraticMaskingRange()
        with pytest.raises(AttributeError):
            s.coeff = 2.0  # type: ignore[misc]

    def test_default_params(self) -> None:
        """默认参数正确。/ Default parameters correct."""
        s = QuadraticMaskingRange()
        assert s.lower == 0.0
        assert s.upper == 1.0
        assert s.coeff == 1.0

    def test_create_with_params(self) -> None:
        """工厂方法设置参数。/ Factory sets parameters."""
        s = QuadraticMaskingRange.create(
            lower=2.0,
            upper=5.0,
            coeff=3.0,
        )
        assert s.lower == 2.0
        assert s.upper == 5.0
        assert s.coeff == 3.0

    def test_evaluate_in_range(self) -> None:
        """范围内求值正确。/ In-range evaluation correct."""
        s = QuadraticMaskingRange.create(
            lower=0.0,
            upper=10.0,
            coeff=1.0,
        )
        assert s.evaluate((3.0,)) == 9.0

    def test_evaluate_below_range(self) -> None:
        """低于范围返回 0。/ Below range returns 0."""
        s = QuadraticMaskingRange.create(lower=2.0, upper=5.0)
        assert s.evaluate((1.0,)) == 0.0

    def test_evaluate_above_range(self) -> None:
        """高于范围返回 0。/ Above range returns 0."""
        s = QuadraticMaskingRange.create(lower=2.0, upper=5.0)
        assert s.evaluate((6.0,)) == 0.0

    def test_evaluate_at_bounds(self) -> None:
        """边界值求值正确。/ Boundary evaluation correct."""
        s = QuadraticMaskingRange.create(
            lower=2.0,
            upper=5.0,
            coeff=1.0,
        )
        assert s.evaluate((2.0,)) == 4.0
        assert s.evaluate((5.0,)) == 25.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = QuadraticMaskingRange()
        assert s.evaluate(()) == 0.0
