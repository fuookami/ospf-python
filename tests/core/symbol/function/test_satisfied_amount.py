"""SatisfiedAmount 测试。

测试满足数量函数符号的创建和求值。
Tests SatisfiedAmount function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.satisfied_amount import (
    SatisfiedAmount,
)


class TestSatisfiedAmount:
    """满足数量测试 / SatisfiedAmount tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = SatisfiedAmount()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = SatisfiedAmount()
        assert str(s) == "SatisfiedAmount"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = SatisfiedAmount()
        with pytest.raises(AttributeError):
            s.name = "changed"  # type: ignore[misc]

    def test_create(self) -> None:
        """工厂方法创建实例。/ Factory creates instance."""
        s = SatisfiedAmount.create()
        assert isinstance(s, SatisfiedAmount)
        assert s.name == "SatisfiedAmount"

    def test_evaluate_all_nonzero(self) -> None:
        """全非零返回总数。/ All nonzero returns total count."""
        s = SatisfiedAmount()
        assert s.evaluate((1.0, 2.0, 3.0)) == 3.0

    def test_evaluate_some_zero(self) -> None:
        """部分为零返回非零计数。/ Some zero returns nonzero count."""
        s = SatisfiedAmount()
        assert s.evaluate((1.0, 0.0, 3.0)) == 2.0

    def test_evaluate_all_zero(self) -> None:
        """全为零返回 0。/ All zero returns 0."""
        s = SatisfiedAmount()
        assert s.evaluate((0.0, 0.0)) == 0.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = SatisfiedAmount()
        assert s.evaluate(()) == 0.0

    def test_evaluate_negative_values(self) -> None:
        """负值计为非零。/ Negative values count as nonzero."""
        s = SatisfiedAmount()
        assert s.evaluate((-1.0, 0.0, -3.0)) == 2.0
