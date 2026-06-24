"""Object 测试。

测试对象的创建和不可变性。
Tests Object creation and immutability.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.basic.object_category import (
    ObjectCategory,
)
from ospf_python.core.model.mechanism.object_ import Object


class TestObject:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        o = Object(name="x", category=ObjectCategory.VARIABLE)
        with pytest.raises(AttributeError):
            o.name = "y"  # type: ignore[misc]

    def test_default_index(self) -> None:
        """默认索引为 -1。/ Default index is -1."""
        o = Object(name="x", category=ObjectCategory.VARIABLE)
        assert o.index == -1
