"""SatisfiedAmountInequality 测试。

测试不等式满足数量函数符号的创建和求值。
Tests SatisfiedAmountInequality function symbol creation
and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.satisfied_amount_inequality import (
    SatisfiedAmountInequality,
)


class TestSatisfiedAmountInequality:
    """不等式满足数量测试 / SatisfiedAmountInequality tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = SatisfiedAmountInequality()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = SatisfiedAmountInequality()
        assert str(s) == "SatisfiedAmountInequality"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = SatisfiedAmountInequality()
        with pytest.raises(AttributeError):
            s.rhs = 1.0  # type: ignore[misc]

    def test_default_rhs(self) -> None:
        """默认右端值为 0。/ Default RHS is 0."""
        s = SatisfiedAmountInequality()
        assert s.rhs == 0.0

    def test_create_with_rhs(self) -> None:
        """工厂方法设置右端值。/ Factory sets RHS."""
        s = SatisfiedAmountInequality.create(rhs=5.0)
        assert s.rhs == 5.0

    def test_evaluate_all_satisfied(self) -> None:
        """全部满足返回总数。/ All satisfied returns total."""
        s = SatisfiedAmountInequality.create(rhs=10.0)
        assert s.evaluate((1.0, 5.0, 9.0)) == 3.0

    def test_evaluate_some_satisfied(self) -> None:
        """部分满足返回计数。/ Some satisfied returns count."""
        s = SatisfiedAmountInequality.create(rhs=5.0)
        assert s.evaluate((1.0, 6.0, 3.0)) == 2.0

    def test_evaluate_none_satisfied(self) -> None:
        """无满足返回 0。/ None satisfied returns 0."""
        s = SatisfiedAmountInequality.create(rhs=0.0)
        assert s.evaluate((1.0, 2.0)) == 0.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = SatisfiedAmountInequality()
        assert s.evaluate(()) == 0.0

    def test_evaluate_boundary_values(self) -> None:
        """边界值计入满足。/ Boundary values count as satisfied."""
        s = SatisfiedAmountInequality.create(rhs=5.0)
        assert s.evaluate((5.0,)) == 1.0
