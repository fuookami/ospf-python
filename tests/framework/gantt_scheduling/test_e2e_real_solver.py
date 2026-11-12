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
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import (
    BunchApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
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


def _complete_column(
    problem: GanttProblem,
    *,
    column_key: str = "complete",
    cost: float = 0.0,
) -> TaskColumn:
    """Build one serial column covering every fixture task."""
    fallback_resource = problem.resources[0].resource_key if problem.resources else ""
    cursor = 0.0
    assignments: list[tuple[str, str, float]] = []
    for task in problem.tasks:
        start = max(cursor, task.earliest_start)
        resource_key = (
            task.resource_keys[0] if task.resource_keys else fallback_resource
        )
        assignments.append((task.task_key, resource_key, start))
        cursor = start + task.duration
    return TaskColumn(column_key, tuple(assignments), cost)


def _build_staggered_window_problem() -> GanttProblem:
    """Build two disjoint short tasks inside the same old event window."""
    return GanttProblem(
        name="staggered-window",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=0.2,
                deadline=1.0,
                resource_requirements=(("r1", 1.0),),
            ),
            Task(
                task_key="t2",
                name="T2",
                duration=0.2,
                deadline=1.0,
                resource_requirements=(("r1", 1.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=1.0),),
        time_horizon=1.0,
    )


class TestGanttE2EGurobi:
    """Gantt e2e with real Gurobi solver."""

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_final_task_model_materializes_registered_variable_types(self) -> None:
        """最终任务模型保留开始连续变量和分配二元变量。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = GanttProblem(
            name="variable_types",
            tasks=(
                Task(
                    task_key="t1",
                    name="Task 1",
                    duration=3.0,
                    resource_requirements=(("r1", 1.0),),
                ),
            ),
            resources=(Resource(resource_key="r1", name="Machine 1", capacity=1.0),),
            time_horizon=10.0,
        )
        solver = GurobiLinearSolver()
        task_ctx = TaskContext()
        resource_ctx = ResourceContext()
        for task in problem.tasks:
            task_ctx.register(task)
        for resource in problem.resources:
            resource_ctx = resource_ctx.register_resource(resource)
        service = TaskApplicationService(
            solver=solver,
            task_context=task_ctx,
            resource_context=resource_ctx,
        )

        assert service.register(problem).is_ok()
        assert service.add_columns((_complete_column(problem),)).is_ok()
        assert service.finalize().is_ok()
        assert service.extract_solution().is_ok()

        assert solver._model is not None
        assert solver._model.IsMIP == 1
        assert solver._model.getVarByName("start_t1").VType == "C"
        assert solver._model.getVarByName("assign_t1_r1").VType == "B"
        solver.cleanup()

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

        assert service.add_columns((_complete_column(problem),)).is_ok()

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

        assert service.add_columns((_complete_column(problem),)).is_ok()

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

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_constrained_task_model_selects_only_feasible_column(self) -> None:
        """容量、优先关系和 makespan 行共同筛出唯一可行列。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = GanttProblem(
            name="constrained-task-model",
            tasks=(
                Task(
                    task_key="t1",
                    name="T1",
                    duration=3.0,
                    resource_requirements=(("r1", 2.0),),
                ),
                Task(
                    task_key="t2",
                    name="T2",
                    duration=2.0,
                    resource_requirements=(("r1", 2.0),),
                ),
            ),
            resources=(Resource(resource_key="r1", name="R1", capacity=3.0),),
            precedence_relations=(
                PrecedenceRelation(predecessor_key="t1", successor_key="t2"),
            ),
            time_horizon=10.0,
        )
        columns = (
            TaskColumn(
                "capacity_bad",
                (("t1", "r1", 0.0), ("t2", "r1", 0.0)),
                0.0,
            ),
            TaskColumn(
                "precedence_bad",
                (("t1", "r1", 3.0), ("t2", "r1", 0.0)),
                0.0,
            ),
            TaskColumn(
                "serial_ok",
                (("t1", "r1", 0.0), ("t2", "r1", 3.0)),
                1.0,
            ),
        )
        solver = GurobiLinearSolver()
        service = TaskApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )

        assert service.register(problem).is_ok()
        assert service.add_columns(columns).is_ok()
        assert service.refresh_shadow_price().is_ok()
        assert service.finalize().is_ok()
        solution = service.extract_solution().unwrap()

        assert solution.is_optimal
        assert solution.makespan == pytest.approx(5.0)
        assert solution.objective_value == pytest.approx(6.0)
        assert [
            (
                entry.task_key,
                entry.start_time,
                entry.end_time,
                entry.assigned_resource,
            )
            for entry in solution.schedule
        ] == [
            ("t1", 0.0, 3.0, "r1"),
            ("t2", 3.0, 5.0, "r1"),
        ]

        model = solver._model
        assert model is not None
        assert model.IsMIP == 1
        assert pytest.approx(0.0) == model.getVarByName("col_capacity_bad").X
        assert pytest.approx(0.0) == model.getVarByName("col_precedence_bad").X
        assert pytest.approx(1.0) == model.getVarByName("col_serial_ok").X
        assert pytest.approx(1.0) == model.getVarByName("assign_t1_r1").X
        assert pytest.approx(1.0) == model.getVarByName("assign_t2_r1").X

        capacity_row = model.getRow(model.getConstrByName("cap_r1_0_2"))
        capacity_coeffs = {
            capacity_row.getVar(index).VarName: capacity_row.getCoeff(index)
            for index in range(capacity_row.size())
        }
        assert capacity_coeffs["col_capacity_bad"] == pytest.approx(4.0)
        assert capacity_coeffs["col_serial_ok"] == pytest.approx(2.0)

        precedence_row = model.getRow(model.getConstrByName("prec_t1_t2"))
        precedence_coeffs = {
            precedence_row.getVar(index).VarName: precedence_row.getCoeff(index)
            for index in range(precedence_row.size())
        }
        assert precedence_coeffs == {
            "start_t1": pytest.approx(-1.0),
            "start_t2": pytest.approx(1.0),
        }

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_bunch_native_model_selects_only_feasible_column(self) -> None:
        """束编组原生模型累计窗口容量并只选择可行列。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = GanttProblem(
            name="bunch-native-gurobi",
            tasks=(
                Task(
                    task_key="t1",
                    name="T1",
                    duration=3.0,
                    resource_requirements=(("r1", 1.0),),
                ),
                Task(
                    task_key="t2",
                    name="T2",
                    duration=2.0,
                    resource_requirements=(("r1", 1.0),),
                ),
            ),
            resources=(Resource(resource_key="r1", name="R1", capacity=1.0),),
            precedence_relations=(PrecedenceRelation("t1", "t2"),),
            time_horizon=10.0,
        )
        columns = (
            BunchColumn(
                "overlap_bad",
                (("t1", 0.0), ("t2", 0.0)),
                "r1",
                0.0,
            ),
            BunchColumn(
                "serial_ok",
                (("t1", 0.0), ("t2", 3.0)),
                "r1",
                1.0,
            ),
            BunchColumn(
                "precedence_bad",
                (("t1", 3.0), ("t2", 0.0)),
                "r1",
                0.0,
            ),
            BunchColumn("split_t1", (("t1", 0.0),), "r1", 3.0),
            BunchColumn("split_t2", (("t2", 3.0),), "r1", 3.0),
        )
        solver = GurobiLinearSolver()
        service = BunchApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            bunch_context=BunchGenerationContext(),
        )

        assert service.register(problem).is_ok()
        assert service.add_columns(columns).is_ok()
        shadow_prices = service.refresh_shadow_price()
        assert shadow_prices.is_ok()
        assert "demand_t1" in shadow_prices.unwrap()
        assert "demand_t2" in shadow_prices.unwrap()
        solution = service.extract_solution().unwrap()

        assert solution.is_optimal
        assert solution.makespan == pytest.approx(5.0)
        assert solution.objective_value == pytest.approx(1.0)
        assert [
            (
                entry.task_key,
                entry.start_time,
                entry.end_time,
                entry.assigned_resource,
            )
            for entry in solution.schedule
        ] == [
            ("t1", 0.0, 3.0, "r1"),
            ("t2", 3.0, 5.0, "r1"),
        ]

        model = solver._model
        assert model is not None
        assert pytest.approx(0.0) == model.getVarByName("bunch_overlap_bad").X
        assert pytest.approx(1.0) == model.getVarByName("bunch_serial_ok").X
        assert pytest.approx(0.0) == model.getVarByName("bunch_precedence_bad").X
        assert pytest.approx(0.0) == model.getVarByName("bunch_split_t1").X
        assert pytest.approx(0.0) == model.getVarByName("bunch_split_t2").X
        assert pytest.approx(1.0) == model.getVarByName("covered_t1").X
        assert pytest.approx(1.0) == model.getVarByName("covered_t2").X
        assert pytest.approx(0.0) == model.getVarByName("start_t1").X
        assert pytest.approx(3.0) == model.getVarByName("start_t2").X

        capacity_row = model.getRow(model.getConstrByName("cap_r1_0_2"))
        capacity_coeffs = {
            capacity_row.getVar(index).VarName: capacity_row.getCoeff(index)
            for index in range(capacity_row.size())
        }
        assert capacity_coeffs["bunch_overlap_bad"] == pytest.approx(2.0)
        assert capacity_coeffs["bunch_serial_ok"] == pytest.approx(1.0)

        precedence_row = model.getRow(model.getConstrByName("prec_t1_t2"))
        precedence_coeffs = {
            precedence_row.getVar(index).VarName: precedence_row.getCoeff(index)
            for index in range(precedence_row.size())
        }
        assert precedence_coeffs == {
            "start_t1": pytest.approx(-1.0),
            "start_t2": pytest.approx(1.0),
        }

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_bunch_capacity_uses_actual_resource_demand(self) -> None:
        """容量行累计真实需求量并排除超过容量的重叠列。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = GanttProblem(
            name="bunch-demand-capacity",
            tasks=(
                Task(
                    task_key="t1",
                    name="T1",
                    duration=3.0,
                    resource_requirements=(("r1", 2.0),),
                ),
                Task(
                    task_key="t2",
                    name="T2",
                    duration=2.0,
                    resource_requirements=(("r1", 2.0),),
                ),
            ),
            resources=(Resource(resource_key="r1", name="R1", capacity=3.0),),
            precedence_relations=(PrecedenceRelation("t1", "t2"),),
            time_horizon=10.0,
        )
        columns = (
            BunchColumn(
                "overlap_bad",
                (("t1", 0.0), ("t2", 0.0)),
                "r1",
                0.0,
            ),
            BunchColumn(
                "serial_ok",
                (("t1", 0.0), ("t2", 3.0)),
                "r1",
                1.0,
            ),
            BunchColumn(
                "precedence_bad",
                (("t1", 3.0), ("t2", 0.0)),
                "r1",
                0.0,
            ),
        )
        solver = GurobiLinearSolver()
        service = BunchApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            bunch_context=BunchGenerationContext(),
        )

        assert service.register(problem).is_ok()
        assert service.add_columns(columns).is_ok()
        assert service.refresh_shadow_price().is_ok()
        solution = service.extract_solution().unwrap()

        assert solution.is_optimal
        assert solution.makespan == pytest.approx(5.0)
        assert solution.objective_value == pytest.approx(1.0)
        assert [entry.start_time for entry in solution.schedule] == [0.0, 3.0]

        model = solver._model
        assert model is not None
        assert pytest.approx(0.0) == model.getVarByName("bunch_overlap_bad").X
        assert pytest.approx(1.0) == model.getVarByName("bunch_serial_ok").X
        assert pytest.approx(0.0) == model.getVarByName("bunch_precedence_bad").X

        capacity_row = model.getRow(model.getConstrByName("cap_r1_0_2"))
        capacity_coeffs = {
            capacity_row.getVar(index).VarName: capacity_row.getCoeff(index)
            for index in range(capacity_row.size())
        }
        assert capacity_coeffs["bunch_overlap_bad"] == pytest.approx(4.0)
        assert capacity_coeffs["bunch_serial_ok"] == pytest.approx(2.0)

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_task_capacity_windows_include_candidate_column_events(self) -> None:
        """任务列事件拆开窗口后，两个不重叠任务可同时调度。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = _build_staggered_window_problem()
        columns = (
            TaskColumn("t1_only", (("t1", "r1", 0.3),), 1.0),
            TaskColumn("t2_only", (("t2", "r1", 0.7),), 1.0),
        )
        solver = GurobiLinearSolver()
        service = TaskApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )

        assert service.register(problem).is_ok()
        assert service.add_columns(columns).is_ok()
        solution = service.extract_solution().unwrap()

        assert solution.is_optimal
        assert solution.makespan == pytest.approx(0.9)
        assert solution.objective_value == pytest.approx(2.9)
        assert [entry.start_time for entry in solution.schedule] == [0.3, 0.7]

        model = solver._model
        assert model is not None
        assert pytest.approx(1.0) == model.getVarByName("col_t1_only").X
        assert pytest.approx(1.0) == model.getVarByName("col_t2_only").X
        for constraint in model.getConstrs():
            if not constraint.ConstrName.startswith("cap_r1_"):
                continue
            row = model.getRow(constraint)
            names = {row.getVar(index).VarName for index in range(row.size())}
            assert not {"col_t1_only", "col_t2_only"} <= names

        solver.cleanup()

    @pytest.mark.skipif(
        not pytest.importorskip("gurobipy", reason="gurobipy not available"),
        reason="gurobipy not available",
    )
    def test_bunch_capacity_windows_include_candidate_column_events(self) -> None:
        """束列事件拆开窗口后，两个不重叠任务可同时覆盖。"""
        from ospf_python.core.solver.gurobi.gurobi_linear_solver import (
            GurobiLinearSolver,
        )

        problem = _build_staggered_window_problem()
        columns = (
            BunchColumn("t1_only", (("t1", 0.3),), "r1", 1.0),
            BunchColumn("t2_only", (("t2", 0.7),), "r1", 1.0),
        )
        solver = GurobiLinearSolver()
        service = BunchApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            bunch_context=BunchGenerationContext(),
        )

        assert service.register(problem).is_ok()
        assert service.add_columns(columns).is_ok()
        solution = service.extract_solution().unwrap()

        assert solution.is_optimal
        assert solution.makespan == pytest.approx(0.9)
        assert solution.objective_value == pytest.approx(2.0)
        assert [entry.start_time for entry in solution.schedule] == [0.3, 0.7]

        model = solver._model
        assert model is not None
        assert pytest.approx(1.0) == model.getVarByName("bunch_t1_only").X
        assert pytest.approx(1.0) == model.getVarByName("bunch_t2_only").X
        for constraint in model.getConstrs():
            if not constraint.ConstrName.startswith("cap_r1_"):
                continue
            row = model.getRow(constraint)
            names = {row.getVar(index).VarName for index in range(row.size())}
            assert not {"bunch_t1_only", "bunch_t2_only"} <= names

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

        assert service.add_columns((_complete_column(problem),)).is_ok()

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

        assert service.add_columns((_complete_column(problem),)).is_ok()

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
