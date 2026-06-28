"""CSP2D 端到端测试 / CSP2D end-to-end tests.

使用 MockSolver 完成完整二维切割库存流程。
Complete 2D cutting stock workflow with MockSolver.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.csp2d_context import Csp2dContext
from ospf_python.framework.csp2d.domain.cutting_plan.cutting_plan_context import (
    CuttingPlanContext,
)
from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingItem,
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
from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
    CuttingPlanGenerator,
)
from ospf_python.framework.csp2d.domain.service.material_optimizer import (
    MaterialOptimizer,
)


class MockSolver:
    """模拟求解器 / Mock solver for CSP2D e2e testing.

    不调用真实求解器，返回预设方案。
    Returns preset plans without calling a real solver.
    """

    def __init__(self) -> None:
        self._called = False

    def solve(
        self,
        sheet: Sheet,
        shapes: tuple[Shape, ...],
        demands: tuple[Demand, ...],
    ) -> tuple[CuttingPlan, ...]:
        """模拟求解 / Mock solve.

        为每个需求创建一个简单方案。
        Creates a simple plan for each demand.

        Args:
            sheet: 目标板材 / Target sheet.
            shapes: 可用形状 / Available shapes.
            demands: 需求 / Demands.

        Returns:
            切割方案元组 / Cutting plan tuple.
        """
        self._called = True
        shape_map = {s.shape_key: s for s in shapes}
        plans: list[CuttingPlan] = []

        for i, demand in enumerate(demands):
            shape = shape_map.get(demand.shape_key)
            if shape is None:
                continue

            items = tuple(
                CuttingItem.create(
                    shape_key=shape.shape_key,
                    x=float(j) * shape.width,
                    y=0.0,
                    rotated=False,
                )
                for j in range(demand.quantity)
            )

            used_area = shape.area * demand.quantity
            waste_ratio = max(
                0.0,
                1.0 - (used_area / sheet.area if sheet.area > 0 else 0.0),
            )

            plan = CuttingPlan.create(
                plan_key=f"mock_plan_{i}",
                material_key=sheet.name,
                items=items,
                waste_ratio=waste_ratio,
            )
            plans.append(plan)

        return tuple(plans)

    @property
    def called(self) -> bool:
        """是否已调用 / Whether called."""
        return self._called


class TestCsp2dE2e:
    """CSP2D 端到端测试 / CSP2D e2e tests."""

    def _make_problem(
        self,
    ) -> tuple[
        tuple[Sheet, ...],
        tuple[Shape, ...],
        tuple[Demand, ...],
    ]:
        """创建测试问题 / Create test problem."""
        sheets = (
            Sheet.create(
                name="Plywood",
                width=1200.0,
                height=2400.0,
                cost=50.0,
            ),
            Sheet.create(
                name="MDF",
                width=1000.0,
                height=2000.0,
                cost=30.0,
            ),
        )
        shapes = (
            Shape.create(
                shape_key="panel_a",
                name="Panel-A",
                width=300.0,
                height=200.0,
                rotatable=True,
            ),
            Shape.create(
                shape_key="panel_b",
                name="Panel-B",
                width=200.0,
                height=150.0,
                rotatable=True,
            ),
            Shape.create(
                shape_key="panel_c",
                name="Panel-C",
                width=150.0,
                height=100.0,
                rotatable=False,
            ),
        )
        demands = (
            Demand.create(
                demand_key="d1",
                shape_key="panel_a",
                quantity=10,
                priority=2,
            ),
            Demand.create(
                demand_key="d2",
                shape_key="panel_b",
                quantity=8,
                priority=1,
            ),
            Demand.create(
                demand_key="d3",
                shape_key="panel_c",
                quantity=15,
                priority=0,
            ),
        )
        return sheets, shapes, demands

    def test_mock_solver_returns_plans(self) -> None:
        """MockSolver 返回方案 / MockSolver returns plans."""
        sheets, shapes, demands = self._make_problem()
        solver = MockSolver()
        plans = solver.solve(sheets[0], shapes, demands)

        assert solver.called is True
        assert len(plans) == 3
        total_items = sum(p.item_count for p in plans)
        assert total_items == 33

    def test_mock_solver_plan_validity(self) -> None:
        """MockSolver 方案有效性 / MockSolver plan validity."""
        sheets, shapes, demands = self._make_problem()
        solver = MockSolver()
        plans = solver.solve(sheets[0], shapes, demands)

        for plan in plans:
            assert plan.waste_ratio >= 0.0
            assert plan.waste_ratio <= 1.0
            assert plan.item_count > 0

    def test_material_optimizer_selects_sheet(self) -> None:
        """材料优化器选择板材 / Material optimizer selects sheet."""
        sheets, shapes, demands = self._make_problem()
        optimizer = MaterialOptimizer()
        result = optimizer.optimize(demands, shapes, sheets)

        assert result is not None
        assert result.plan_count >= 1
        assert result.total_cost > 0.0

    def test_cutting_plan_generator_produces_plans(self) -> None:
        """方案生成器产生方案 / Plan generator produces plans."""
        sheets, shapes, demands = self._make_problem()
        generator = CuttingPlanGenerator()
        plans = generator.generate_guillotine(sheets[0], shapes, demands)

        assert len(plans) >= 1
        total_items = sum(p.item_count for p in plans)
        assert total_items == 33

    def test_context_registration(self) -> None:
        """上下文注册 / Context registration."""
        sheets, shapes, demands = self._make_problem()

        # Material context
        mat_ctx = MaterialContext()
        for sheet in sheets:
            mat_ctx.register_sheet(sheet)
        assert mat_ctx.sheet_count == 2

        # Product context
        prod_ctx = ProductContext()
        for shape in shapes:
            prod_ctx.register_shape(shape)
        for demand in demands:
            prod_ctx.register_demand(demand)
        assert prod_ctx.shape_count == 3
        assert prod_ctx.demand_count == 3

    def test_full_domain_wiring(self) -> None:
        """完整领域模型连接 / Full domain model wiring."""
        sheets, shapes, demands = self._make_problem()

        # Setup contexts
        mat_ctx = MaterialContext()
        for sheet in sheets:
            mat_ctx.register_sheet(sheet)

        prod_ctx = ProductContext()
        for shape in shapes:
            prod_ctx.register_shape(shape)
        for demand in demands:
            prod_ctx.register_demand(demand)

        plan_ctx = CuttingPlanContext()

        # Create aggregate context
        csp_ctx = Csp2dContext.create(
            material_context=mat_ctx,
            product_context=prod_ctx,
            cutting_plan_context=plan_ctx,
        )
        assert csp_ctx.material_context.sheet_count == 2
        assert csp_ctx.product_context.shape_count == 3

        # Solve with mock
        solver = MockSolver()
        plans = solver.solve(sheets[0], shapes, demands)

        # Register plans
        for plan in plans:
            plan_ctx.register(plan)
        assert plan_ctx.size == 3

        # Verify plans for material
        mat_plans = plan_ctx.plans_for_material(sheets[0].name)
        assert len(mat_plans) == 3

        # Verify optimization
        optimizer = MaterialOptimizer()
        best = optimizer.optimize(demands, shapes, sheets)
        assert best is not None
        assert best.total_waste_ratio < 1.0
