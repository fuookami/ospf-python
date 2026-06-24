"""QuantityRange tests.

Test quantity range model creation and immutability.
测试数量范围模型创建和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.quantity_range import (
    QuantityRange,
)


class TestQuantityRange:
    """QuantityRange frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        r = QuantityRange(min_qty=1, max_qty=10)
        assert r.min_qty == 1
        assert r.max_qty == 10

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        r = QuantityRange(min_qty=1, max_qty=10)
        with pytest.raises(AttributeError):
            r.min_qty = 5  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = QuantityRange(min_qty=1, max_qty=10)
        b = QuantityRange(min_qty=1, max_qty=10)
        assert a == b

    def test_inequality(self) -> None:
        """Different values yield inequality. / 不同值不等。"""
        a = QuantityRange(min_qty=1, max_qty=10)
        b = QuantityRange(min_qty=2, max_qty=10)
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        r = QuantityRange(min_qty=1, max_qty=10)
        assert hash(r) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        assert dataclasses.is_dataclass(QuantityRange(min_qty=0, max_qty=1))
