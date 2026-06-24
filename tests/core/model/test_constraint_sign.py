"""ConstraintSign 测试。

测试约束符号枚举的定义和值。
Tests ConstraintSign enum definition and values.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)


class TestConstraintSign:
    """枚举测试 / Enum tests."""

    def test_le_value(self) -> None:
        """LE 值为 '<='。/ LE is '<='."""
        assert ConstraintSign.LE.value == "<="

    def test_ge_value(self) -> None:
        """GE 值为 '>='。/ GE is '>='."""
        assert ConstraintSign.GE.value == ">="

    def test_eq_value(self) -> None:
        """EQ 值为 '=='。/ EQ is '=='."""
        assert ConstraintSign.EQ.value == "=="
