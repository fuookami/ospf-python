"""DumpHelpers 测试。

测试转储辅助工具的格式化方法。
Tests DumpHelpers formatting methods.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.dump_helpers import (
    DumpHelpers,
)


class TestDumpHelpersFormatCoefficient:
    """系数格式化测试 / Coefficient formatting tests."""

    def test_integer_value(self) -> None:
        """整数值输出无小数。/ Integer value has no decimal."""
        assert DumpHelpers.format_coefficient(3.0) == "3"

    def test_float_value(self) -> None:
        """浮点值输出正确。/ Float value correct."""
        result = DumpHelpers.format_coefficient(3.14)
        assert "3.14" in result

    def test_zero(self) -> None:
        """零值输出正确。/ Zero value correct."""
        assert DumpHelpers.format_coefficient(0.0) == "0"

    def test_negative(self) -> None:
        """负值输出正确。/ Negative value correct."""
        assert DumpHelpers.format_coefficient(-5.0) == "-5"

    def test_small_float(self) -> None:
        """小浮点数格式化。/ Small float formatting."""
        result = DumpHelpers.format_coefficient(0.001)
        assert "0.001" in result


class TestDumpHelpersFormatSign:
    """符号格式化测试 / Sign formatting tests."""

    def test_le(self) -> None:
        """小于等于符号。/ Less than or equal sign."""
        assert DumpHelpers.format_sign("<=") == "<="

    def test_ge(self) -> None:
        """大于等于符号。/ Greater than or equal sign."""
        assert DumpHelpers.format_sign(">=") == ">="

    def test_eq(self) -> None:
        """等号映射为 =。/ Equal maps to =."""
        assert DumpHelpers.format_sign("==") == "="

    def test_unknown_passthrough(self) -> None:
        """未知符号透传。/ Unknown sign passes through."""
        assert DumpHelpers.format_sign("!=") == "!="
