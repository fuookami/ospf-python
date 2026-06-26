"""Gantt scheduling 端到端真实求解器测试 / End-to-end gantt scheduling tests with real solvers.

通过框架 GurobiSolver/ScipSolver 求解甘特调度实例，
验证列生成编排在真实求解器下的正确性。
Solves gantt scheduling instances through framework
GurobiSolver/ScipSolver, verifying column generation
orchestration correctness with real solvers.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)


def _build_simple_problem() -> GanttProblem:
    """构建简单甘特调度问题 / Build simple gantt scheduling problem.

    3 个任务，1 个资源，1 个优先关系。
    3 tasks, 1 resource, 1 precedence relation.
    """
    tasks = (
        Task(task_key="t1", name="Task 1", duration=3.0, priority=1),
        Task(task_key="t2", name="Task 2", duration=2.0, priority=2),
        Task(task_key="t3", name="Task 3", duration=4.0, priority=1),
    )
    resources = (Resource(resource_key="r1", name="Machine 1", capacity=10.0),)
    return GanttProblem(
        name="e2e_test",
        tasks=tasks,
        resources=resources,
        precedence_relations=(
            PrecedenceRelation(predecessor_key="t1", successor_key="t2"),
        ),
        time_horizon=20.0,
    )


def _build_multi_resource_problem() -> GanttProblem:
    """构建多资源甘特调度问题 / Build multi-resource gantt problem.

    5 个任务，2 个资源，多个优先关系。
    5 tasks, 2 resources, multiple precedence relations.
    """
    tasks = (
        Task(task_key="t1", name="Design", duration=5.0, priority=1),
        Task(task_key="t2", name="Implement", duration=8.0, priority=2),
        Task(task_key="t3", name="Test", duration=3.0, priority=3),
        Task(task_key="t4", name="Deploy", duration=2.0, priority=4),
        Task(task_key="t5", name="Review", duration=4.0, priority=2),
    )
    resources = (
        Resource(resource_key="dev", name="Developer", capacity=16.0),
        Resource(resource_key="qa", name="QA Engineer", capacity=8.0),
    )
    return GanttProblem(
        name="multi_resource_test",
        tasks=tasks,
        resources=resources,
        precedence_relations=(
            PrecedenceRelation(predecessor_key="t1", successor_key="t2"),
            PrecedenceRelation(predecessor_key="t2", successor_key="t3"),
            PrecedenceRelation(predecessor_key="t3", successor_key="t4"),
        ),
        time_horizon=50.0,
    )


class TestGanttE2EGurobi:
    """Gantt e2e with real Gurobi solver."""

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_simple_gantt_gurobi(self) -> None:
        """Simple gantt scheduling with Gurobi."""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = _build_simple_problem()
        solver = GurobiLinearSolver()
        task_ctx = TaskContext()
        resource_ctx = ResourceContext()

        for t in problem.tasks:
            task_ctx.register(t)
        for r in problem.resources:
            resource_ctx = resource_ctx.register_resource(r)

        service = TaskApplicationService(
            solver=solver,
            task_context=task_ctx,
            resource_context=resource_ctx,
        )

        # 注册问题
        reg_result = service.register(problem)
        assert reg_result.is_ok(), f"Register failed: {reg_result}"

        # 刷新影子价格
        sp_result = service.refresh_shadow_price()
        assert sp_result.is_ok(), f"Shadow price failed: {sp_result}"

        # 终止
        fin_result = service.finalize()
        assert fin_result.is_ok(), f"Finalize failed: {fin_result}"

        # 提取解
        sol_result = service.extract_solution()
        assert sol_result.is_ok(), f"Extract failed: {sol_result}"

        solution = sol_result.unwrap()
        assert solution is not None
        assert solution.is_optimal

        # 验证排程回填
        assert solution.schedule is not None
        assert len(solution.schedule) > 0

        # 验证 makespan 合理
        assert solution.makespan > 0
        print(
            f"Gantt Gurobi: makespan={solution.makespan}, schedule={solution.schedule}"
        )

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_multi_resource_gantt_gurobi(self) -> None:
        """Multi-resource gantt scheduling with Gurobi."""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = _build_multi_resource_problem()
        solver = GurobiLinearSolver()
        task_ctx = TaskContext()
        resource_ctx = ResourceContext()

        for t in problem.tasks:
            task_ctx.register(t)
        for r in problem.resources:
            resource_ctx = resource_ctx.register_resource(r)

        service = TaskApplicationService(
            solver=solver,
            task_context=task_ctx,
            resource_context=resource_ctx,
        )

        reg_result = service.register(problem)
        assert reg_result.is_ok()

        sp_result = service.refresh_shadow_price()
        assert sp_result.is_ok()

        fin_result = service.finalize()
        assert fin_result.is_ok()

        sol_result = service.extract_solution()
        assert sol_result.is_ok()

        solution = sol_result.unwrap()
        assert solution is not None
        assert solution.is_optimal
        assert solution.makespan > 0
        print(f"Gantt Gurobi multi-resource: makespan={solution.makespan}")

        solver.cleanup()


class TestGanttE2EScip:
    """Gantt e2e with real SCIP solver."""

    @pytest.mark.skipif(
        not pytest.importorskip("pyscipopt", reason="pyscipopt not available"),
        reason="pyscipopt not available",
    )
    def test_simple_gantt_scip(self) -> None:
        """Simple gantt scheduling with SCIP."""
        from ospf_python.core.solver.scip.scip_linear_solver import (
            ScipLinearSolver,
        )

        problem = _build_simple_problem()
        solver = ScipLinearSolver()
        task_ctx = TaskContext()
        resource_ctx = ResourceContext()

        for t in problem.tasks:
            task_ctx.register(t)
        for r in problem.resources:
            resource_ctx = resource_ctx.register_resource(r)

        service = TaskApplicationService(
            solver=solver,
            task_context=task_ctx,
            resource_context=resource_ctx,
        )

        reg_result = service.register(problem)
        assert reg_result.is_ok(), f"Register failed: {reg_result}"

        sp_result = service.refresh_shadow_price()
        assert sp_result.is_ok(), f"Shadow price failed: {sp_result}"

        fin_result = service.finalize()
        assert fin_result.is_ok(), f"Finalize failed: {fin_result}"

        sol_result = service.extract_solution()
        assert sol_result.is_ok(), f"Extract failed: {sol_result}"

        solution = sol_result.unwrap()
        assert solution is not None
        assert solution.is_optimal
        assert solution.schedule is not None
        assert len(solution.schedule) > 0
        assert solution.makespan > 0
        print(f"Gantt SCIP: makespan={solution.makespan}, schedule={solution.schedule}")

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("pyscipopt", reason="pyscipopt not available"),
        reason="pyscipopt not available",
    )
    def test_multi_resource_gantt_scip(self) -> None:
        """Multi-resource gantt scheduling with SCIP."""
        from ospf_python.core.solver.scip.scip_linear_solver import (
            ScipLinearSolver,
        )

        problem = _build_multi_resource_problem()
        solver = ScipLinearSolver()
        task_ctx = TaskContext()
        resource_ctx = ResourceContext()

        for t in problem.tasks:
            task_ctx.register(t)
        for r in problem.resources:
            resource_ctx = resource_ctx.register_resource(r)

        service = TaskApplicationService(
            solver=solver,
            task_context=task_ctx,
            resource_context=resource_ctx,
        )

        reg_result = service.register(problem)
        assert reg_result.is_ok()

        sp_result = service.refresh_shadow_price()
        assert sp_result.is_ok()

        fin_result = service.finalize()
        assert fin_result.is_ok()

        sol_result = service.extract_solution()
        assert sol_result.is_ok()

        solution = sol_result.unwrap()
        assert solution is not None
        assert solution.is_optimal
        assert solution.makespan > 0
        print(f"Gantt SCIP multi-resource: makespan={solution.makespan}")

        solver.cleanup()
