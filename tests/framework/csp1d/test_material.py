"""Material tests.

Test Material model creation, fields, and immutability.
测试材料模型创建、字段和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.material import (
    Material,
)


class TestMaterial:
    """Material frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        m = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        assert m.name == "Steel"
        assert m.width == 100.0
        assert m.length == 600.0
        assert m.cost == 50.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        m = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        with pytest.raises(AttributeError):
            m.name = "Copper"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        b = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        assert a == b

    def test_inequality(self) -> None:
        """Different field values yield inequality. / 不同字段值不等。"""
        a = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        b = Material(name="Copper", width=100.0, length=600.0, cost=50.0)
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        m = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        assert hash(m) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        m = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        assert dataclasses.is_dataclass(m)
