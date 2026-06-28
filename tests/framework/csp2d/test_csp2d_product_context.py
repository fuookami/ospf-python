"""CSP2D 产品上下文行为测试 / CSP2D product context behavioral tests.

测试 ProductContext 的注册、查询和辅助方法。
Test ProductContext registration, lookup, and helpers.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.product.product_context import (
    ProductContext,
)


class TestProductContextBehavioral:
    """产品上下文行为测试 / Product context behavioral tests."""

    def test_register_duplicate_shape_rejected(self) -> None:
        """重复形状被拒绝 / Duplicate shape rejected."""
        ctx = ProductContext()
        shape = Shape.create(
            shape_key="sh1",
            name="Panel",
            width=30.0,
            height=20.0,
        )
        ctx.register_shape(shape)
        result = ctx.register_shape(shape)
        assert result.is_failed()

    def test_register_duplicate_demand_rejected(self) -> None:
        """重复需求被拒绝 / Duplicate demand rejected."""
        ctx = ProductContext()
        demand = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
        )
        ctx.register_demand(demand)
        result = ctx.register_demand(demand)
        assert result.is_failed()

    def test_get_shape_returns_none_for_missing(self) -> None:
        """获取不存在形状返回 None / Get shape returns None for missing."""
        ctx = ProductContext()
        assert ctx.get_shape("nonexistent") is None

    def test_get_shape_or_error_not_found(self) -> None:
        """获取不存在形状返回错误 / Get shape or error returns error for missing."""
        ctx = ProductContext()
        result = ctx.get_shape_or_error("nonexistent")
        assert result.is_failed()

    def test_get_shape_or_error_found(self) -> None:
        """获取存在的形状 / Get shape or error found."""
        ctx = ProductContext()
        shape = Shape.create(
            shape_key="sh1",
            name="Panel",
            width=30.0,
            height=20.0,
        )
        ctx.register_shape(shape)
        result = ctx.get_shape_or_error("sh1")
        assert result.is_ok()
        assert result.unwrap().shape_key == "sh1"

    def test_get_demand_returns_none_for_missing(self) -> None:
        """获取不存在需求返回 None / Get demand returns None for missing."""
        ctx = ProductContext()
        assert ctx.get_demand("nonexistent") is None

    def test_get_demand_or_error_not_found(self) -> None:
        """获取不存在需求返回错误 / Get demand or error returns error for missing."""
        ctx = ProductContext()
        result = ctx.get_demand_or_error("nonexistent")
        assert result.is_failed()

    def test_get_demand_or_error_found(self) -> None:
        """获取存在的需求 / Get demand or error found."""
        ctx = ProductContext()
        demand = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
        )
        ctx.register_demand(demand)
        result = ctx.get_demand_or_error("d1")
        assert result.is_ok()
        assert result.unwrap().demand_key == "d1"

    def test_shapes_returns_all(self) -> None:
        """获取所有形状 / Get all shapes."""
        ctx = ProductContext()
        s1 = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        s2 = Shape.create(shape_key="sh2", name="B", width=20.0, height=15.0)
        ctx.register_shape(s1)
        ctx.register_shape(s2)
        all_shapes = ctx.shapes()
        assert len(all_shapes) == 2

    def test_demands_returns_all(self) -> None:
        """获取所有需求 / Get all demands."""
        ctx = ProductContext()
        d1 = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        d2 = Demand.create(demand_key="d2", shape_key="sh2", quantity=3)
        ctx.register_demand(d1)
        ctx.register_demand(d2)
        all_demands = ctx.demands()
        assert len(all_demands) == 2

    def test_demands_for_shape_no_match(self) -> None:
        """按形状查询需求无匹配 / Demands for shape no match."""
        ctx = ProductContext()
        d1 = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_demand(d1)
        result = ctx.demands_for_shape("sh99")
        assert len(result) == 0

    def test_contains_shape(self) -> None:
        """检查形状是否存在 / Check shape exists."""
        ctx = ProductContext()
        shape = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        ctx.register_shape(shape)
        assert ctx.contains_shape("sh1") is True
        assert ctx.contains_shape("nonexistent") is False

    def test_contains_demand(self) -> None:
        """检查需求是否存在 / Check demand exists."""
        ctx = ProductContext()
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_demand(demand)
        assert ctx.contains_demand("d1") is True
        assert ctx.contains_demand("nonexistent") is False

    def test_shape_count(self) -> None:
        """形状计数 / Shape count."""
        ctx = ProductContext()
        assert ctx.shape_count == 0
        shape = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        ctx.register_shape(shape)
        assert ctx.shape_count == 1

    def test_demand_count(self) -> None:
        """需求计数 / Demand count."""
        ctx = ProductContext()
        assert ctx.demand_count == 0
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_demand(demand)
        assert ctx.demand_count == 1

    def test_size_combines_shapes_and_demands(self) -> None:
        """size 为形状和需求总数 / Size combines shapes and demands."""
        ctx = ProductContext()
        shape = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_shape(shape)
        ctx.register_demand(demand)
        assert ctx.size == 2

    def test_is_empty_with_only_shapes(self) -> None:
        """仅有形状时不为空 / Not empty with only shapes."""
        ctx = ProductContext()
        shape = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        ctx.register_shape(shape)
        assert ctx.is_empty is False

    def test_is_empty_with_only_demands(self) -> None:
        """仅有需求时不为空 / Not empty with only demands."""
        ctx = ProductContext()
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_demand(demand)
        assert ctx.is_empty is False

    def test_clear(self) -> None:
        """清空产品 / Clear products."""
        ctx = ProductContext()
        shape = Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0)
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=5)
        ctx.register_shape(shape)
        ctx.register_demand(demand)
        ctx.clear()
        assert ctx.is_empty is True
        assert ctx.shape_count == 0
        assert ctx.demand_count == 0
