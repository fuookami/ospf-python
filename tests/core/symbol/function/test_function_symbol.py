"""FunctionSymbol 基类测试。

测试函数符号基类的接口和行为。
Tests FunctionSymbol base class interface and behaviour.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.function.abs import Abs
from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


class TestFunctionSymbolBase:
    """基类测试 / Base class tests."""

    def test_abs_is_function_symbol(self) -> None:
        """Abs 是 FunctionSymbol 子类。/ Abs is subclass."""
        s = Abs()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = Abs()
        assert str(s) == "Abs"

    def test_frozen(self) -> None:
        """符号不可变。/ Symbol is frozen."""
        s = Abs()
        with pytest.raises(AttributeError):
            s.name = "changed"  # type: ignore[misc]
