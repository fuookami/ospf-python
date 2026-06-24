"""Product tests.

Test Product model creation, fields, and immutability.
测试产品模型创建、字段和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.product import (
    Product,
)


class TestProduct:
    """Product frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        p = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        assert p.name == "Panel-A"
        assert p.width == 30.0
        assert p.length == 200.0
        assert p.demand == 50

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        p = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        with pytest.raises(AttributeError):
            p.name = "Panel-B"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        b = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        assert a == b

    def test_inequality(self) -> None:
        """Different names yield inequality. / 不同名称不等。"""
        a = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        b = Product(name="Panel-B", width=30.0, length=200.0, demand=50)
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        p = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        assert hash(p) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        p = Product(name="Panel-A", width=30.0, length=200.0, demand=50)
        assert dataclasses.is_dataclass(p)
