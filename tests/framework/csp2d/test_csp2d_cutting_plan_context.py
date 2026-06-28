"""CSP2D 切割方案上下文行为测试 / CSP2D cutting plan context behavioral tests.

测试 CuttingPlanContext 的注册、注销和查询逻辑。
Test CuttingPlanContext registration, unregistration, and lookup.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.cutting_plan.cutting_plan_context import (
    CuttingPlanContext,
)
from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingItem,
    CuttingPlan,
)


class TestCuttingPlanContextBehavioral:
    """切割方案上下文行为测试 / Cutting plan context behavioral tests."""

    def test_register_duplicate_rejected(self) -> None:
        """重复方案被拒绝 / Duplicate plan rejected."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.1,
        )
        ctx.register(plan)
        result = ctx.register(plan)
        assert result.is_failed()

    def test_unregister_nonexistent(self) -> None:
        """注销不存在的方案 / Unregister nonexistent plan."""
        ctx = CuttingPlanContext()
        result = ctx.unregister("nonexistent")
        assert result.is_failed()

    def test_unregister_existing(self) -> None:
        """注销存在的方案 / Unregister existing plan."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.1,
        )
        ctx.register(plan)
        result = ctx.unregister("p1")
        assert result.is_ok()
        assert ctx.size == 0

    def test_get_returns_none_for_missing(self) -> None:
        """获取不存在方案返回 None / Get returns None for missing."""
        ctx = CuttingPlanContext()
        assert ctx.get("nonexistent") is None

    def test_get_or_error_found(self) -> None:
        """获取存在的方案 / Get plan or error found."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.1,
        )
        ctx.register(plan)
        result = ctx.get_or_error("p1")
        assert result.is_ok()
        assert result.unwrap().plan_key == "p1"

    def test_get_or_error_not_found(self) -> None:
        """获取不存在的方案返回错误 / Get plan or error not found."""
        ctx = CuttingPlanContext()
        result = ctx.get_or_error("nonexistent")
        assert result.is_failed()

    def test_items_returns_all(self) -> None:
        """获取所有方案 / Get all plans."""
        ctx = CuttingPlanContext()
        p1 = CuttingPlan.create(plan_key="p1", material_key="S1")
        p2 = CuttingPlan.create(plan_key="p2", material_key="S2")
        ctx.register(p1)
        ctx.register(p2)
        all_plans = ctx.items()
        assert len(all_plans) == 2

    def test_plans_for_material_no_match(self) -> None:
        """按材料查询无匹配 / Plans for material no match."""
        ctx = CuttingPlanContext()
        p1 = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(p1)
        result = ctx.plans_for_material("S99")
        assert len(result) == 0

    def test_contains(self) -> None:
        """检查方案是否存在 / Check plan exists."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(plan)
        assert ctx.contains("p1") is True
        assert ctx.contains("nonexistent") is False

    def test_size_property(self) -> None:
        """方案数量属性 / Plan size property."""
        ctx = CuttingPlanContext()
        assert ctx.size == 0
        plan = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(plan)
        assert ctx.size == 1

    def test_is_empty_property(self) -> None:
        """是否为空属性 / Is empty property."""
        ctx = CuttingPlanContext()
        assert ctx.is_empty is True
        plan = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(plan)
        assert ctx.is_empty is False

    def test_clear(self) -> None:
        """清空方案 / Clear plans."""
        ctx = CuttingPlanContext()
        plan = CuttingPlan.create(plan_key="p1", material_key="S1")
        ctx.register(plan)
        ctx.clear()
        assert ctx.is_empty is True
        assert ctx.size == 0

    def test_plan_with_items(self) -> None:
        """带切割项的方案 / Plan with cutting items."""
        ctx = CuttingPlanContext()
        items = (
            CuttingItem.create(shape_key="sh1", x=0.0, y=0.0, rotated=False),
            CuttingItem.create(shape_key="sh2", x=30.0, y=0.0, rotated=True),
        )
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            items=items,
            waste_ratio=0.2,
        )
        ctx.register(plan)
        retrieved = ctx.get("p1")
        assert retrieved is not None
        assert retrieved.item_count == 2
