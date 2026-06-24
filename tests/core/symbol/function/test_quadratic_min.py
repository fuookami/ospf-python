"""QuadraticMin 测试。

测试二次最小值函数符号的创建和求值。
Tests QuadraticMin function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.quadratic_min import QuadraticMin


class TestQuadraticMin:
    """二次最小值测试 / QuadraticMin tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = QuadraticMin()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = QuadraticMin()
        assert str(s) == "QuadraticMin"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = QuadraticMin()
        with pytest.raises(AttributeError):
            s.coeff = 2.0  # type: ignore[misc]

    def test_default_coeff(self) -> None:
        """默认系数为 1。/ Default coefficient is 1."""
        s = QuadraticMin()
        assert s.coeff == 1.0

    def test_create_with_coeff(self) -> None:
        """工厂方法设置系数。/ Factory sets coefficient."""
        s = QuadraticMin.create(coeff=3.0)
        assert s.coeff == 3.0

    def test_evaluate_multiple_args(self) -> None:
        """多参数返回最小二次值。/ Multiple args returns min quadratic."""
        s = QuadraticMin()
        # min(1^2, 2^2, 3^2) = 1
        assert s.evaluate((1.0, 2.0, 3.0)) == 1.0

    def test_evaluate_with_coeff(self) -> None:
        """带系数求值正确。/ With coefficient evaluation correct."""
        s = QuadraticMin.create(coeff=2.0)
        # min(2*1^2, 2*3^2) = 2
        assert s.evaluate((1.0, 3.0)) == 2.0

    def test_evaluate_single_arg(self) -> None:
        """单参数返回该二次值。/ Single arg returns its quadratic."""
        s = QuadraticMin()
        assert s.evaluate((4.0,)) == 16.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = QuadraticMin()
        assert s.evaluate(()) == 0.0

    def test_evaluate_negative_values(self) -> None:
        """负值平方后取最小。/ Negative values squared then min."""
        s = QuadraticMin()
        # min((-3)^2, 1^2) = 1
        assert s.evaluate((-3.0, 1.0)) == 1.0
