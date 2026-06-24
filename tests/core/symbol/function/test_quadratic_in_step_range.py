"""QuadraticInStepRange 测试。

测试二次步进范围内函数符号的创建和求值。
Tests QuadraticInStepRange function symbol creation
and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.quadratic_in_step_range import (
    QuadraticInStepRange,
)


class TestQuadraticInStepRange:
    """二次步进范围内测试 / QuadraticInStepRange tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = QuadraticInStepRange()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = QuadraticInStepRange()
        assert str(s) == "QuadraticInStepRange"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = QuadraticInStepRange()
        with pytest.raises(AttributeError):
            s.step = 2.0  # type: ignore[misc]

    def test_default_params(self) -> None:
        """默认参数正确。/ Default parameters correct."""
        s = QuadraticInStepRange()
        assert s.step == 1.0
        assert s.coeff == 1.0

    def test_create_with_params(self) -> None:
        """工厂方法设置参数。/ Factory sets parameters."""
        s = QuadraticInStepRange.create(step=2.0, coeff=3.0)
        assert s.step == 2.0
        assert s.coeff == 3.0

    def test_evaluate_basic(self) -> None:
        """基本求值正确。/ Basic evaluation correct."""
        s = QuadraticInStepRange.create(step=1.0, coeff=1.0)
        assert s.evaluate((3.0,)) == 9.0

    def test_evaluate_with_step(self) -> None:
        """步长求值正确。/ Step evaluation correct."""
        s = QuadraticInStepRange.create(step=2.0, coeff=1.0)
        assert s.evaluate((5.0,)) == 4.0

    def test_evaluate_zero_step(self) -> None:
        """零步长返回 0。/ Zero step returns 0."""
        s = QuadraticInStepRange.create(step=0.0)
        assert s.evaluate((5.0,)) == 0.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = QuadraticInStepRange()
        assert s.evaluate(()) == 0.0
