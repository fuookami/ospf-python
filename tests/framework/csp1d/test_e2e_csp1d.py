"""End-to-end CSP1D tests.

Create a simple 1D cutting stock problem with 2 materials
and 3 products, solve with MockSolver, and verify solution.
创建一个简单的 1D 切割库存问题（2 种材料、3 种产品），
使用 MockSolver 求解，并验证解决方案。
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)
from ospf_python.framework.csp1d.application.model.csp1d_problem_builder import (
    Csp1dProblemBuilder,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.framework.csp1d.application.service.csp1d_column_generation import (
    ColumnRecord,
    Csp1dColumnGeneration,
)
from ospf_python.framework.csp1d.application.service.csp1d_final_milp_status import (
    Csp1dFinalMilpStatus,
)
from ospf_python.framework.csp1d.application.service.csp1d_milp import (
    Csp1dMilp,
)
from ospf_python.framework.csp1d.application.service.csp1d_milp_solver import (
    Csp1dMilpSolver,
    SolverResult,
)
from ospf_python.framework.csp1d.application.service.csp1d_schedule import (
    Csp1dSchedule,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.constraints import (
    Constraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.dfs_generator import (
    DfsGenerator,
)
from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
    CuttingPlan,
)
from ospf_python.framework.csp1d.domain.material.model.product import (
    Product,
)
from ospf_python.framework.csp1d.domain.material.model.quantity_range import (
    QuantityRange,
)
from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
    ShadowPriceMap,
)
from ospf_python.framework.csp1d.domain.material.model.width_range import (
    WidthRange,
)
from ospf_python.framework.csp1d.domain.wasting_minimization.model.waste_model import (
    WasteModel,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_problem import (
        Csp1dProblem,
    )

# importlib workaround for 'yield' keyword in path
_YieldModel = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.model.yield_model",
).YieldModel


class MockSolver:
    """A mock solver for e2e testing.

    用于端到端测试的模拟求解器。
    """

    def __init__(self) -> None:
        self._solved = False

    def solve(self, problem: Csp1dProblem) -> Csp1dSolution:
        """Solve and return a mock solution.

        求解并返回模拟解决方案。
        """
        self._solved = True
        # Build a realistic solution from the problem
        assignments = []
        for demand in problem.demands:
            assignments.append(
                Csp1dAssignment(
                    material=problem.materials[0].name
                    if problem.materials
                    else "default",
                    cutting_plan=f"plan-{demand.product}",
                    quantity=demand.quantity,
                    waste=5.0,
                )
            )
        total_waste = sum(a.waste * a.quantity for a in assignments)
        return Csp1dSolution(
            assignments=tuple(assignments),
            total_waste=total_waste,
            utilization=0.92,
        )

    @property
    def solved(self) -> bool:
        """Whether solver has been invoked.

        求解器是否已被调用。
        """
        return self._solved


class TestE2eCsp1d:
    """End-to-end CSP1D workflow tests."""

    def _build_problem(self) -> Csp1dProblem:
        """Build a standard 2-material, 3-product problem.

        构建标准的 2 材料、3 产品问题。
        """
        builder = Csp1dProblemBuilder()
        # 2 materials / 2 种材料
        builder.add_material(name="Steel", width=100.0, length=600.0, cost=50.0)
        builder.add_material(name="Aluminum", width=80.0, length=500.0, cost=70.0)
        # 3 products / 3 种产品
        builder.add_product(name="Panel-A", width=30.0, length=200.0, demand=20)
        builder.add_product(name="Panel-B", width=25.0, length=150.0, demand=15)
        builder.add_product(name="Panel-C", width=20.0, length=100.0, demand=30)
        # 1 machine / 1 台机器
        builder.add_machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        # Demands / 需求
        builder.add_demand(product="Panel-A", quantity=20)
        builder.add_demand(product="Panel-B", quantity=15)
        builder.add_demand(product="Panel-C", quantity=30)
        return builder.build()

    def test_build_problem(self) -> None:
        """Build problem with 2 materials and 3 products.

        构建包含 2 种材料和 3 种产品的问题。
        """
        problem = self._build_problem()
        assert len(problem.materials) == 2
        assert len(problem.products) == 3
        assert len(problem.machines) == 1
        assert len(problem.demands) == 3

    def test_mock_solver_returns_solution(self) -> None:
        """Mock solver returns a valid solution.

        模拟求解器返回有效解决方案。
        """
        problem = self._build_problem()
        solver = MockSolver()
        solution = solver.solve(problem)
        assert solver.solved
        assert isinstance(solution, Csp1dSolution)
        assert len(solution.assignments) == 3
        assert solution.utilization > 0.0

    def test_solution_has_assignments(self) -> None:
        """Solution contains assignments with correct fields.

        解决方案包含正确字段的分配。
        """
        problem = self._build_problem()
        solver = MockSolver()
        solution = solver.solve(problem)
        for assignment in solution.assignments:
            assert isinstance(assignment, Csp1dAssignment)
            assert assignment.quantity > 0
            assert assignment.waste >= 0.0
            assert len(assignment.material) > 0
            assert len(assignment.cutting_plan) > 0

    def test_solution_utilization(self) -> None:
        """Solution utilization is between 0 and 1.

        解决方案利用率在 0 到 1 之间。
        """
        problem = self._build_problem()
        solver = MockSolver()
        solution = solver.solve(problem)
        assert 0.0 <= solution.utilization <= 1.0

    def test_schedule_solution(self) -> None:
        """Schedule solution to machines.

        将解决方案排程到机器。
        """
        problem = self._build_problem()
        solver = MockSolver()
        solution = solver.solve(problem)
        scheduler = Csp1dSchedule(problem.machines)
        schedule = scheduler.schedule(solution)
        total_batches = sum(a.quantity for a in solution.assignments)
        assert len(schedule) == total_batches

    def test_cutting_plan_creation(self) -> None:
        """Create cutting plans for the problem.

        为问题创建切割计划。
        """
        p1 = Product(name="Panel-A", width=30.0, length=200.0, demand=20)
        cp = CuttingPlan(
            material="Steel",
            products=((p1, 3),),
            waste=10.0,
        )
        assert cp.material == "Steel"
        assert cp.waste == 10.0
        assert len(cp.products) == 1

    def test_shadow_price_map(self) -> None:
        """Shadow price map works correctly.

        影子价格映射正常工作。
        """
        spm = ShadowPriceMap()
        spm.set("Panel-A", 5.0)
        spm.set("Panel-B", 3.0)
        assert spm.get("Panel-A") == 5.0
        assert spm.get("Panel-B") == 3.0
        assert spm.get("Panel-C") == 0.0
        assert "Panel-A" in spm
        assert len(spm) == 2

    def test_column_generation_lifecycle(self) -> None:
        """Test column generation lifecycle.

        测试列生成生命周期。
        """
        cg = Csp1dColumnGeneration(max_iterations=5)
        col = ColumnRecord(
            name="init-1",
            coefficients=(1.0, 0.0),
            reduced_cost=-2.0,
        )
        result = cg.register((col,))
        assert result.is_ok()
        assert len(cg.active_columns) == 1
        assert cg.iteration == 0

        cg.refresh_shadow_price(lambda p: p.set("P1", 5.0))
        assert cg.iteration == 1

        cg.finalize()
        assert cg.converged is True

    def test_milp_model_workflow(self) -> None:
        """Test MILP model construction workflow.

        测试 MILP 模型构建工作流。
        """
        milp = Csp1dMilp()
        milp.add_variable(name="x1", lower=0.0, upper=10.0)
        milp.add_variable(name="x2", is_integer=True)
        milp.add_constraint(
            name="demand",
            coefficients=(("x1", 1.0), ("x2", 1.0)),
            sense=">=",
            rhs=5.0,
        )
        milp.set_objective({"x1": 1.0, "x2": 2.0})
        assert len(milp.variables) == 2
        assert len(milp.constraints) == 1
        assert milp.objective["x1"] == 1.0

    def test_solver_workflow(self) -> None:
        """Test solver with mock function.

        使用模拟函数测试求解器。
        """

        def mock_fn(model: Csp1dMilp) -> SolverResult:
            return SolverResult(
                status=Csp1dFinalMilpStatus.OPTIMAL,
                objective_value=42.0,
                variable_values=(("x1", 5.0),),
            )

        solver = Csp1dMilpSolver(mock_fn)
        model = Csp1dMilp()
        result = solver.solve(model)
        assert result.is_ok()
        assert result.unwrap().objective_value == 42.0

    def test_dfs_generation(self) -> None:
        """Test DFS cutting plan generation.

        测试 DFS 切割方案生成。
        """
        constraints = Constraints(max_knife_count=5)
        gc = GenerationConstraints(
            material_constraints=constraints,
            max_depth=10,
            max_solutions=50,
        )
        gen = DfsGenerator(constraints=gc)
        products = [
            ("Panel-A", 30.0, 3),
            ("Panel-B", 25.0, 3),
        ]
        plans = gen.generate(material_length=100.0, products=products)
        assert len(plans) > 0
        # All plans should be non-empty
        for plan in plans:
            assert len(plan) > 0

    def test_full_domain_model_wiring(self) -> None:
        """Wire all domain models together.

        连接所有领域模型。
        """
        problem = self._build_problem()
        solver = MockSolver()
        solution = solver.solve(problem)

        # Verify all domain objects
        assert problem.materials[0].name == "Steel"
        assert problem.products[0].name == "Panel-A"
        assert problem.machines[0].name == "Cutter-1"
        assert solution.utilization == 0.92
        assert solution.total_waste > 0.0

        # Schedule
        scheduler = Csp1dSchedule(problem.machines)
        schedule = scheduler.schedule(solution)
        assert len(schedule) > 0

        # Domain models
        assert WasteModel() is not None
        assert _YieldModel() is not None
        assert QuantityRange(min_qty=1, max_qty=10) is not None
        assert WidthRange(min_width=0.0, max_width=100.0) is not None
