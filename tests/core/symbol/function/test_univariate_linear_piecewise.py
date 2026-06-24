"""UnivariateLinearPiecewise 测试。

测试单变量线性分段函数符号的创建和求值。
Tests UnivariateLinearPiecewise function symbol creation
and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.univariate_linear_piecewise import (
    UnivariateLinearPiecewise,
)


class TestUnivariateLinearPiecewise:
    """单变量线性分段测试 / UnivariateLinearPiecewise tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = UnivariateLinearPiecewise()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = UnivariateLinearPiecewise()
        assert str(s) == "UnivariateLinearPiecewise"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = UnivariateLinearPiecewise()
        with pytest.raises(AttributeError):
            s.slope = 2.0  # type: ignore[misc]

    def test_default_params(self) -> None:
        """默认参数正确。/ Default parameters correct."""
        s = UnivariateLinearPiecewise()
        assert s.slope == 1.0
        assert s.intercept == 0.0

    def test_create_with_params(self) -> None:
        """工厂方法设置参数。/ Factory sets parameters."""
        s = UnivariateLinearPiecewise.create(
            slope=2.0,
            intercept=3.0,
        )
        assert s.slope == 2.0
        assert s.intercept == 3.0

    def test_evaluate_basic(self) -> None:
        """基本求值正确。/ Basic evaluation correct."""
        s = UnivariateLinearPiecewise()
        assert s.evaluate((5.0,)) == 5.0

    def test_evaluate_with_slope_intercept(self) -> None:
        """带斜率截距求值。/ With slope and intercept."""
        s = UnivariateLinearPiecewise.create(
            slope=2.0,
            intercept=3.0,
        )
        # 2*4 + 3 = 11
        assert s.evaluate((4.0,)) == 11.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回截距。/ Empty args returns intercept."""
        s = UnivariateLinearPiecewise.create(intercept=5.0)
        assert s.evaluate(()) == 5.0

    def test_evaluate_empty_default(self) -> None:
        """空参数默认截距为 0。/ Empty args default intercept 0."""
        s = UnivariateLinearPiecewise()
        assert s.evaluate(()) == 0.0

    def test_evaluate_negative_input(self) -> None:
        """负输入求值正确。/ Negative input evaluation correct."""
        s = UnivariateLinearPiecewise.create(
            slope=2.0,
            intercept=1.0,
        )
        assert s.evaluate((-3.0,)) == -5.0
