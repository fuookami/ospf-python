"""BPP2D 物品上下文行为测试 / BPP2D item context behavioral tests.

测试 ItemContext 的注册、注销、查询和辅助方法。
Test ItemContext registration, unregistration, lookup, and helpers.
"""

from __future__ import annotations

from ospf_python.framework.bpp2d.domain.item.item_context import ItemContext
from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle


class TestItemContextBehavioral:
    """物品上下文行为测试 / Item context behavioral tests."""

    def test_unregister_item(self) -> None:
        """注销物品 / Unregister item."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        ctx.register(rect)
        assert ctx.size == 1

        result = ctx.unregister("r1")
        assert result.is_ok()
        assert ctx.size == 0
        assert ctx.is_empty is True

    def test_unregister_nonexistent_item(self) -> None:
        """注销不存在的物品 / Unregister nonexistent item."""
        ctx = ItemContext()
        result = ctx.unregister("nonexistent")
        assert result.is_failed()

    def test_get_or_error_found(self) -> None:
        """获取存在的物品 / Get existing item."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        ctx.register(rect)
        result = ctx.get_or_error("r1")
        assert result.is_ok()
        assert result.unwrap().item_key == "r1"

    def test_get_or_error_not_found(self) -> None:
        """获取不存在的物品返回错误 / Get nonexistent item returns error."""
        ctx = ItemContext()
        result = ctx.get_or_error("nonexistent")
        assert result.is_failed()

    def test_get_returns_none_for_missing(self) -> None:
        """获取缺失物品返回 None / Get returns None for missing."""
        ctx = ItemContext()
        assert ctx.get("missing") is None

    def test_items_returns_all(self) -> None:
        """获取所有物品 / Get all items."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        circle = Circle.create(item_key="c1", radius=3.0)
        ctx.register(rect)
        ctx.register(circle)

        all_items = ctx.items()
        assert len(all_items) == 2

    def test_item_keys(self) -> None:
        """获取所有物品键 / Get all item keys."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        circle = Circle.create(item_key="c1", radius=3.0)
        ctx.register(rect)
        ctx.register(circle)

        keys = ctx.item_keys()
        assert "r1" in keys
        assert "c1" in keys

    def test_rectangles_filter(self) -> None:
        """过滤矩形物品 / Filter rectangle items."""
        ctx = ItemContext()
        r1 = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        r2 = Rectangle.create(item_key="r2", width=8.0, height=4.0)
        c1 = Circle.create(item_key="c1", radius=3.0)
        ctx.register(r1)
        ctx.register(r2)
        ctx.register(c1)

        rects = ctx.rectangles()
        assert len(rects) == 2
        assert all(isinstance(r, Rectangle) for r in rects)

    def test_circles_filter(self) -> None:
        """过滤圆形物品 / Filter circle items."""
        ctx = ItemContext()
        r1 = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        c1 = Circle.create(item_key="c1", radius=3.0)
        c2 = Circle.create(item_key="c2", radius=5.0)
        ctx.register(r1)
        ctx.register(c1)
        ctx.register(c2)

        circs = ctx.circles()
        assert len(circs) == 2
        assert all(isinstance(c, Circle) for c in circs)

    def test_contains(self) -> None:
        """检查物品是否存在 / Check item exists."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        ctx.register(rect)
        assert ctx.contains("r1") is True
        assert ctx.contains("nonexistent") is False

    def test_is_empty_on_new_context(self) -> None:
        """新上下文为空 / New context is empty."""
        ctx = ItemContext()
        assert ctx.is_empty is True
        assert ctx.size == 0

    def test_total_weight(self) -> None:
        """计算总重量 / Calculate total weight."""
        ctx = ItemContext()
        r1 = Rectangle.create(item_key="r1", width=10.0, height=5.0, weight=3.0)
        r2 = Rectangle.create(item_key="r2", width=8.0, height=4.0, weight=2.0)
        c1 = Circle.create(item_key="c1", radius=3.0, weight=1.5)
        ctx.register(r1)
        ctx.register(r2)
        ctx.register(c1)

        assert ctx.total_weight == 6.5

    def test_total_weight_empty(self) -> None:
        """空上下文总重量为 0 / Empty context total weight is 0."""
        ctx = ItemContext()
        assert ctx.total_weight == 0.0

    def test_clear(self) -> None:
        """清空物品 / Clear items."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        ctx.register(rect)
        ctx.clear()
        assert ctx.is_empty is True
        assert ctx.size == 0
