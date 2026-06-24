"""SlackRange 测试。

测试松弛范围函数符号的创建和求值。
Tests SlackRange function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.slack_range import SlackRange


class TestSlackRange:
    """松弛范围测试 / SlackRange tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = SlackRange()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = SlackRange()
        assert str(s) == "SlackRange"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = SlackRange()
        with pytest.raises(AttributeError):
            s.lower = 1.0  # type: ignore[misc]

    def test_default_bounds(self) -> None:
        """默认边界正确。/ Default bounds correct."""
        s = SlackRange()
        assert s.lower == 0.0
        assert s.upper == 1.0

    def test_create_with_bounds(self) -> None:
        """工厂方法设置边界。/ Factory sets bounds."""
        s = SlackRange.create(lower=2.0, upper=5.0)
        assert s.lower == 2.0
        assert s.upper == 5.0

    def test_evaluate_within_range(self) -> None:
        """范围内松弛为到两端距离之和。/ Within range slack is sum of distances."""
        s = SlackRange.create(lower=2.0, upper=5.0)
        # max(0, 3-2) + max(0, 5-3) = 1 + 2 = 3
        assert s.evaluate((3.0,)) == 3.0

    def test_evaluate_below_lower(self) -> None:
        """低于下界有松弛。/ Below lower has slack."""
        s = SlackRange.create(lower=2.0, upper=5.0)
        # max(0, 1-2) + max(0, 5-1) = 0 + 4 = 4
        assert s.evaluate((1.0,)) == 4.0

    def test_evaluate_above_upper(self) -> None:
        """高于上界有松弛。/ Above upper has slack."""
        s = SlackRange.create(lower=2.0, upper=5.0)
        # max(0, 7-2) + max(0, 5-7) = 5 + 0 = 5
        assert s.evaluate((7.0,)) == 5.0

    def test_evaluate_at_bounds(self) -> None:
        """边界值松弛正确。/ Boundary slack correct."""
        s = SlackRange.create(lower=2.0, upper=5.0)
        assert s.evaluate((2.0,)) == 3.0
        assert s.evaluate((5.0,)) == 3.0

    def test_evaluate_empty_args(self) -> None:
        """空参数返回 0。/ Empty args returns 0."""
        s = SlackRange()
        assert s.evaluate(()) == 0.0
