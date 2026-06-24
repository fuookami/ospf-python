"""Cell 测试。

测试单元格的创建和不可变性。
Tests Cell creation and immutability.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.intermediate.cell import Cell


class TestCell:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        c = Cell(row=0, col=1, value=3.14)
        with pytest.raises(AttributeError):
            c.value = 2.71  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值。/ Correctly stores values."""
        c = Cell(row=2, col=3, value=5.0)
        assert c.row == 2
        assert c.col == 3
        assert c.value == 5.0
