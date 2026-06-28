"""CSP2D 约束逻辑测试 / CSP2D constraint logic tests.

测试材料和产品上下文的注册与查询逻辑。
Test material and product context registration and lookup.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.cutting_plan.cutting_plan_context import (
    CuttingPlanContext,
)
from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingPlan,
)
from ospf_python.framework.csp2d.domain.material.material_context import (
    MaterialContext,
)
from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.material.model.strip import Strip
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.product.product_context import (
    ProductContext,
)


class TestMaterialContext:
    """材料上下文测试 / Material context tests."""

    def test_register_sheet(self) -> None:
        """注册板材 / Register sheet."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        result = ctx.register_sheet(sheet)
        assert result.is_ok()
        assert ctx.sheet_count == 1
        assert ctx.contains_sheet("S1")

    def test_register_strip(self) -> None:
        """注册卷材 / Register strip."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        result = ctx.register_strip(strip)
        assert result.is_ok()
        assert ctx.strip_count == 1
        assert ctx.contains_strip("R1")

    def test_duplicate_sheet_rejected(self) -> None:
        """重复板材被拒绝 / Duplicate sheet rejected."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        result = ctx.register_sheet(sheet)
        assert result.is_failed()

    def test_duplicate_strip_rejected(self) -> None:
        """重复卷材被拒绝 / Duplicate strip rejected."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        result = ctx.register_strip(strip)
        assert result.is_failed()

    def test_get_sheet_or_error(self) -> None:
        """获取板材或错误 / Get sheet or error."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        result = ctx.get_sheet_or_error("S1")
        assert result.is_ok()
        assert result.unwrap().width == 100.0

        result_missing = ctx.get_sheet_or_error("nonexistent")
        assert result_missing.is_failed()

    def test_get_strip_or_error(self) -> None:
        """获取卷材或错误 / Get strip or error."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        result = ctx.get_strip_or_error("R1")
        assert result.is_ok()

        result_missing = ctx.get_strip_or_error("nonexistent")
        assert result_missing.is_failed()

    def test_items_returns_all(self) -> None:
        """获取所有材料 / Get all materials."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_sheet(sheet)
        ctx.register_strip(strip)
        assert ctx.size == 2
        assert len(ctx.items()) == 2
        assert ctx.is_empty is False

    def test_clear(self) -> None:
        """清空材料 / Clear materials."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        ctx.clear()
        assert ctx.is_empty is True


class TestProductContext:
    """产品上下文测试 / Product context tests."""

    def test_register_shape(self) -> None:
        """注册形状 / Register shape."""
        ctx = ProductContext()
        shape = Shape.create(
            shape_key="sh1",
            name="Panel",
            width=30.0,
            height=20.0,
        )
        result = ctx.register_shape(shape)
        assert result.is_ok()
        assert ctx.shape_count == 1
        assert ctx.contains_shape("sh1")

    def test_register_demand(self) -> None:
        """注册需求 / Register demand."""
        ctx = ProductContext()
        demand = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
        )
        result = ctx.register_demand(demand)
        assert result.is_ok()
        assert ctx.demand_count == 1
        assert ctx.contains_demand("d1")

    def test_duplicate_shape_rejected(self) -> None:
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

    def test_demands_for_shape(self) -> None:
        """按形状查询需求 / Demands for shape."""
        ctx = ProductContext()
        d1 = Demand.create(demand_key="d1", shape_key="sh1", quantity=10)
        d2 = Demand.create(demand_key="d2", shape_key="sh1", quantity=5)
        d3 = Demand.create(demand_key="d3", shape_key="sh2", quantity=3)
        ctx.register_demand(d1)
        ctx.register_demand(d2)
        ctx.register_demand(d3)

        sh1_demands = ctx.demands_for_shape("sh1")
        assert len(sh1_demands) == 2
        sh2_demands = ctx.demands_for_shape("sh2")
        assert len(sh2_demands) == 1

    def test_size_and_empty(self) -> None:
        """大小和空检查 / Size and empty check."""
        ctx = ProductContext()
        assert ctx.is_empty is True
        shape = Shape.create(
            shape_key="sh1",
            name="P",
            width=10.0,
            height=10.0,
        )
        ctx.register_shape(shape)
        assert ctx.size == 1
        assert ctx.is_empty is False

    def test_clear(self) -> None:
        """清空产品 / Clear products."""
        ctx = ProductContext()
        shape = Shape.create(
            shape_key="sh1",
            name="P",
            width=10.0,
            height=10.0,
        )
        ctx.register_shape(shape)
        ctx.clear()
        assert ctx.is_empty is True


class TestCuttingPlanContext:
    """切割方案上下文测试 / Cutting plan context tests."""

    def test_register_plan(self) -> None:
        """注册方案 / Register plan."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.1,
        )
        result = ctx.register(plan)
        assert result.is_ok()
        assert ctx.size == 1
        assert ctx.contains("p1")

    def test_duplicate_plan_rejected(self) -> None:
        """重复方案被拒绝 / Duplicate plan rejected."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
        )
        ctx.register(plan)
        result = ctx.register(plan)
        assert result.is_failed()

    def test_unregister_plan(self) -> None:
        """注销方案 / Unregister plan."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
        )
        ctx.register(plan)
        result = ctx.unregister("p1")
        assert result.is_ok()
        assert ctx.size == 0

    def test_unregister_nonexistent(self) -> None:
        """注销不存在的方案 / Unregister nonexistent plan."""
        ctx = CuttingPlanContext()
        result = ctx.unregister("nonexistent")
        assert result.is_failed()

    def test_plans_for_material(self) -> None:
        """按材料查询方案 / Plans for material."""
        ctx = CuttingPlanContext()
        p1 = CuttingPlan.create(plan_key="p1", material_key="S1")
        p2 = CuttingPlan.create(plan_key="p2", material_key="S1")
        p3 = CuttingPlan.create(plan_key="p3", material_key="S2")
        ctx.register(p1)
        ctx.register(p2)
        ctx.register(p3)

        s1_plans = ctx.plans_for_material("S1")
        assert len(s1_plans) == 2
        s2_plans = ctx.plans_for_material("S2")
        assert len(s2_plans) == 1

    def test_get_or_error(self) -> None:
        """获取方案或错误 / Get plan or error."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(plan)
        result = ctx.get_or_error("p1")
        assert result.is_ok()

        result_missing = ctx.get_or_error("nonexistent")
        assert result_missing.is_failed()
