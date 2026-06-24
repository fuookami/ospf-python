"""Relation 测试。

测试关系的创建和不可变性。
Tests Relation creation and immutability.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.mechanism.relation import Relation


class TestRelation:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        r = Relation(source="a", target="b")
        with pytest.raises(AttributeError):
            r.source = "c"  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值。/ Correctly stores values."""
        r = Relation(
            source="x",
            target="y",
            relation_type="depends_on",
        )
        assert r.relation_type == "depends_on"
