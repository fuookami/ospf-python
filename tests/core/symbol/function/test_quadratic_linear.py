"""QuadraticLinear 测试。

测试二次线性函数符号的创建和求值。
Tests QuadraticLinear function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.quadratic_linear import (
    QuadraticLinear,
)


class TestQuadraticLinear:
    """二次线性测试 / QuadraticLinear tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = QuadraticLinear()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = QuadraticLinear()
        assert str(s) == "QuadraticLinear"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = QuadraticLinear()
        with pytest.raises(AttributeError):
            s.quadratic_coeff = 2.0  # type: ignore[misc]

    def test_default_params(self) -> None:
        """默认参数正确。/ Default parameters correct."""
        s = QuadraticLinear()
        assert s.quadratic_coeff == 1.0
        assert s.linear_coeff == 0.0
        assert s.intercept == 0.0

    def test_create_with_params(self) -> None:
        """工厂方法设置参数。/ Factory sets parameters."""
        s = QuadraticLinear.create(
            quadratic_coeff=2.0,
            linear_coeff=3.0,
            intercept=1.0,
        )
        assert s.quadratic_coeff == 2.0
        assert s.linear_coeff == 3.0
        assert s.intercept == 1.0

    def test_evaluate_pure_quadratic(self) -> None:
        """纯二次求值。/ Pure quadratic evaluation."""
        s = QuadraticLinear()
        assert s.evaluate((3.0,)) == 9.0

    def test_evaluate_full_expression(self) -> None:
        """完整表达式求值。/ Full expression evaluation."""
        s = QuadraticLinear.create(
            quadratic_coeff=2.0,
            linear_coeff=3.0,
            intercept=1.0,
        )
        # 2*4^2 + 3*4 + 1 = 32 + 12 + 1 = 45
        assert s.evaluate((4.0,)) == 45.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = QuadraticLinear()
        assert s.evaluate(()) == 0.0

    def test_evaluate_negative_input(self) -> None:
        """负输入求值正确。/ Negative input evaluation correct."""
        s = QuadraticLinear()
        assert s.evaluate((-2.0,)) == 4.0
