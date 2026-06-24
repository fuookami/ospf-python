"""Product 测试。

测试乘积函数符号的创建和求值。
Tests Product function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.product import Product


class TestProduct:
    """乘积测试 / Product tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = Product()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = Product()
        assert str(s) == "Product"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = Product()
        with pytest.raises(AttributeError):
            s.name = "changed"  # type: ignore[misc]

    def test_create(self) -> None:
        """工厂方法创建实例。/ Factory creates instance."""
        s = Product.create()
        assert isinstance(s, Product)
        assert s.name == "Product"

    def test_evaluate_multiple_args(self) -> None:
        """多参数乘积正确。/ Multiple args product correct."""
        s = Product()
        assert s.evaluate((2.0, 3.0, 4.0)) == 24.0

    def test_evaluate_single_arg(self) -> None:
        """单参数返回该值。/ Single arg returns that value."""
        s = Product()
        assert s.evaluate((5.0,)) == 5.0

    def test_evaluate_with_zero(self) -> None:
        """包含零返回 0。/ Contains zero returns 0."""
        s = Product()
        assert s.evaluate((2.0, 0.0, 5.0)) == 0.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 1。/ Empty args returns 1."""
        s = Product()
        assert s.evaluate(()) == 1.0

    def test_evaluate_negative_values(self) -> None:
        """负值乘积正确。/ Negative values product correct."""
        s = Product()
        assert s.evaluate((-2.0, 3.0)) == -6.0
