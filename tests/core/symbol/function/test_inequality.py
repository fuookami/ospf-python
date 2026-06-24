"""Inequality 测试。

测试不等式函数符号的创建和求值。
Tests Inequality function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.inequality import Inequality


class TestInequality:
    """不等式测试 / Inequality tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = Inequality()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = Inequality()
        assert str(s) == "Inequality"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = Inequality()
        with pytest.raises(AttributeError):
            s.rhs = 1.0  # type: ignore[misc]

    def test_default_params(self) -> None:
        """默认参数正确。/ Default parameters correct."""
        s = Inequality()
        assert s.rhs == 0.0
        assert s.tolerance == 1e-6

    def test_create_with_params(self) -> None:
        """工厂方法设置参数。/ Factory sets parameters."""
        s = Inequality.create(rhs=10.0, tolerance=1e-4)
        assert s.rhs == 10.0
        assert s.tolerance == 1e-4

    def test_evaluate_satisfied(self) -> None:
        """满足不等式返回 1。/ Satisfied returns 1."""
        s = Inequality.create(rhs=10.0)
        assert s.evaluate((5.0,)) == 1.0

    def test_evaluate_not_satisfied(self) -> None:
        """不满足不等式返回 0。/ Not satisfied returns 0."""
        s = Inequality.create(rhs=10.0)
        assert s.evaluate((15.0,)) == 0.0

    def test_evaluate_within_tolerance(self) -> None:
        """容差范围内返回 1。/ Within tolerance returns 1."""
        s = Inequality.create(rhs=10.0, tolerance=0.1)
        assert s.evaluate((10.05,)) == 1.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = Inequality()
        assert s.evaluate(()) == 0.0
