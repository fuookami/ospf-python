"""Masking 测试。

测试掩码函数符号的创建和求值。
Tests Masking function symbol creation and evaluation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.core.symbol.function.masking import Masking


class TestMasking:
    """掩码测试 / Masking tests."""

    def test_is_function_symbol(self) -> None:
        """是 FunctionSymbol 子类。/ Is FunctionSymbol subclass."""
        s = Masking()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = Masking()
        assert str(s) == "Masking"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        s = Masking()
        with pytest.raises(AttributeError):
            s.mask_value = 1.0  # type: ignore[misc]

    def test_default_mask_value(self) -> None:
        """默认掩码值为 0。/ Default mask value is 0."""
        s = Masking()
        assert s.mask_value == 0.0

    def test_create_with_mask_value(self) -> None:
        """工厂方法设置掩码值。/ Factory sets mask value."""
        s = Masking.create(mask_value=-1.0)
        assert s.mask_value == -1.0

    def test_evaluate_nonzero_passthrough(self) -> None:
        """非零输入透传。/ Nonzero input passes through."""
        s = Masking()
        assert s.evaluate((5.0,)) == 5.0

    def test_evaluate_zero_returns_mask(self) -> None:
        """零输入返回掩码值。/ Zero input returns mask."""
        s = Masking.create(mask_value=-1.0)
        assert s.evaluate((0.0,)) == -1.0

    def test_evaluate_empty_returns_mask(self) -> None:
        """空参数返回掩码值。/ Empty args returns mask."""
        s = Masking.create(mask_value=99.0)
        assert s.evaluate(()) == 99.0

    def test_evaluate_negative_passthrough(self) -> None:
        """负输入透传。/ Negative input passes through."""
        s = Masking()
        assert s.evaluate((-3.0,)) == -3.0
