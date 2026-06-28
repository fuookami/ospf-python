"""CSP2D 上下文行为测试 / CSP2D context behavioral tests.

测试 Csp2dContext 的创建和清空逻辑。
Test Csp2dContext creation and clear logic.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.csp2d_context import Csp2dContext
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
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.product.product_context import (
    ProductContext,
)


class TestCsp2dContextBehavioral:
    """CSP2D 上下文行为测试 / CSP2D context behavioral tests."""

    def _make_context(self) -> Csp2dContext:
        """创建测试上下文 / Create test context."""
        mat_ctx = MaterialContext()
        mat_ctx.register_sheet(
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )

        prod_ctx = ProductContext()
        prod_ctx.register_shape(
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        prod_ctx.register_demand(
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )

        plan_ctx = CuttingPlanContext()

        return Csp2dContext.create(
            material_context=mat_ctx,
            product_context=prod_ctx,
            cutting_plan_context=plan_ctx,
        )

    def test_create_csp2d_context(self) -> None:
        """创建 CSP2D 上下文 / Create CSP2D context."""
        ctx = self._make_context()
        assert ctx.material_context.sheet_count == 1
        assert ctx.product_context.shape_count == 1
        assert ctx.product_context.demand_count == 1
        assert ctx.cutting_plan_context.is_empty is True

    def test_clear_clears_all_sub_contexts(self) -> None:
        """清空所有子上下文 / Clear all sub-contexts."""
        ctx = self._make_context()

        # Register a plan in cutting_plan_context
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.5,
        )
        ctx.cutting_plan_context.register(plan)

        # Verify data exists before clear
        assert ctx.material_context.sheet_count == 1
        assert ctx.product_context.shape_count == 1
        assert ctx.product_context.demand_count == 1
        assert ctx.cutting_plan_context.size == 1

        # Clear
        ctx.clear()

        # Verify all sub-contexts are empty
        assert ctx.material_context.is_empty is True
        assert ctx.product_context.is_empty is True
        assert ctx.cutting_plan_context.is_empty is True

    def test_context_attributes_immutable(self) -> None:
        """上下文属性不可变 / Context attributes are immutable (frozen)."""
        ctx = self._make_context()
        assert ctx.material_context is not None
        assert ctx.product_context is not None
        assert ctx.cutting_plan_context is not None
