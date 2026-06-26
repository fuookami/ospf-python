"""资源属性模型测试。

Resource attribute model tests.

测试 ResourceAttribute 的构造、属性访问、get、has、
with_attribute、keys 和 values 方法。
Tests ResourceAttribute construction, property access, get,
has, with_attribute, keys, and values.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_attribute import (
    ResourceAttribute,
)

# ── construction tests ─────────────────────────────────────────


class TestResourceAttributeConstruction:
    """构造测试。/ Construction tests."""

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        ra = ResourceAttribute(resource_key="res-1")
        assert ra.resource_key == "res-1"
        assert ra.attributes == ()

    def test_with_attributes(self) -> None:
        """带属性构造。/ Construction with attributes."""
        attrs = (("color", "red"), ("weight", 10))
        ra = ResourceAttribute(
            resource_key="res-2",
            attributes=attrs,
        )
        assert ra.resource_key == "res-2"
        assert len(ra.attributes) == 2

    def test_frozen(self) -> None:
        """不可变性。/ Frozen behavior."""
        ra = ResourceAttribute(resource_key="res-1")
        with pytest.raises(AttributeError):
            ra.resource_key = "x"  # type: ignore[misc]


# ── get tests ──────────────────────────────────────────────────


class TestResourceAttributeGet:
    """get 方法测试。/ get method tests."""

    def test_get_existing(self) -> None:
        """获取存在的属性。/ Get existing attribute."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(("color", "blue"),),
        )
        assert ra.get("color") == "blue"

    def test_get_missing(self) -> None:
        """获取不存在的属性返回 None。/ Get missing returns None."""
        ra = ResourceAttribute(resource_key="r1")
        assert ra.get("missing") is None

    def test_get_multiple(self) -> None:
        """多属性获取。/ Get from multiple attributes."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(
                ("a", 1),
                ("b", 2),
                ("c", 3),
            ),
        )
        assert ra.get("a") == 1
        assert ra.get("b") == 2
        assert ra.get("c") == 3


# ── has tests ──────────────────────────────────────────────────


class TestResourceAttributeHas:
    """has 方法测试。/ has method tests."""

    def test_has_existing(self) -> None:
        """存在的属性。/ Existing attribute."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(("color", "red"),),
        )
        assert ra.has("color") is True

    def test_has_missing(self) -> None:
        """不存在的属性。/ Missing attribute."""
        ra = ResourceAttribute(resource_key="r1")
        assert ra.has("missing") is False


# ── with_attribute tests ───────────────────────────────────────


class TestResourceAttributeWith:
    """with_attribute 方法测试。

    with_attribute method tests.
    """

    def test_add_attribute(self) -> None:
        """添加属性。/ Add attribute."""
        ra = ResourceAttribute(resource_key="r1")
        new_ra = ra.with_attribute(key="color", value="red")
        assert new_ra.get("color") == "red"
        assert new_ra.resource_key == "r1"

    def test_original_unchanged(self) -> None:
        """原始不变。/ Original unchanged."""
        ra = ResourceAttribute(resource_key="r1")
        _ = ra.with_attribute(key="color", value="red")
        assert ra.has("color") is False

    def test_update_existing(self) -> None:
        """更新已有属性。/ Update existing attribute."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(("color", "red"),),
        )
        new_ra = ra.with_attribute(key="color", value="blue")
        assert new_ra.get("color") == "blue"
        assert len(new_ra.attributes) == 1

    def test_preserve_other_attributes(self) -> None:
        """保留其他属性。/ Preserve other attributes."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(
                ("a", 1),
                ("b", 2),
            ),
        )
        new_ra = ra.with_attribute(key="c", value=3)
        assert new_ra.get("a") == 1
        assert new_ra.get("b") == 2
        assert new_ra.get("c") == 3


# ── keys / values tests ────────────────────────────────────────


class TestResourceAttributeKeysValues:
    """keys/values 方法测试。

    keys/values method tests.
    """

    def test_keys_empty(self) -> None:
        """空属性键。/ Empty attribute keys."""
        ra = ResourceAttribute(resource_key="r1")
        assert ra.keys() == ()

    def test_keys(self) -> None:
        """属性键列表。/ Attribute key list."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(
                ("a", 1),
                ("b", 2),
            ),
        )
        assert ra.keys() == ("a", "b")

    def test_values_empty(self) -> None:
        """空属性值。/ Empty attribute values."""
        ra = ResourceAttribute(resource_key="r1")
        assert ra.values() == ()

    def test_values(self) -> None:
        """属性值列表。/ Attribute value list."""
        ra = ResourceAttribute(
            resource_key="r1",
            attributes=(
                ("a", 1),
                ("b", "hello"),
            ),
        )
        assert ra.values() == (1, "hello")
