"""ExpressionRange 测试。

测试表达式范围的创建和不可变性。
Tests ExpressionRange creation and immutability.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.basic.expression_range import (
    ExpressionRange,
)


class TestExpressionRange:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        r = ExpressionRange(lower=0.0, upper=10.0)
        with pytest.raises(AttributeError):
            r.lower = 5.0  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储上下界。/ Correctly stores bounds."""
        r = ExpressionRange(lower=-1.5, upper=3.5)
        assert r.lower == -1.5
        assert r.upper == 3.5
