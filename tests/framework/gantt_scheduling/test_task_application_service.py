"""任务应用服务测试 / Task application service tests.

覆盖 TaskApplicationService 的列生成生命周期方法。
Covers TaskApplicationService column generation lifecycle
methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python import _native
from ospf_python._binding.control import CancellationScope
from ospf_python.core.model.intermediate.linear_triad_model import LinearTriadModel
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.output.solver_output import SolverOutput
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.application.model.task.task_problem import (
    TaskProblem,
)
from ospf_python.framework.gantt_scheduling.application.service.task import (
    task_application_service as _task_application_service_module,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    TaskColumn,
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
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python._binding.model import MetaModelFloat64


def _make_problem() -> GanttProblem:
    """构建测试用甘特问题。/ Build test gantt problem."""
    tasks = (
        Task(
            task_key="t1",
            name="Task 1",
            duration=3.0,
            priority=1,
            resource_requirements=(("r1", 1.0),),
        ),
        Task(
            task_key="t2",
            name="Task 2",
            duration=2.0,
            priority=2,
            resource_requirements=(("r1", 1.0),),
        ),
        Task(
            task_key="t3",
            name="Task 3",
            duration=4.0,
            priority=1,
            resource_requirements=(("r1", 1.0),),
        ),
    )
    resources = (Resource(resource_key="r1", name="R1", capacity=10.0),)
    return GanttProblem(
        name="task_test",
        tasks=tasks,
        resources=resources,
        precedence_relations=(
            PrecedenceRelation(
                predecessor_key="t1",
                successor_key="t2",
            ),
        ),
        time_horizon=20.0,
    )


def _make_pricing_problem() -> GanttProblem:
    """构建无时隙任务-执行器定价问题 / Build an unslotted task-executor pricing problem."""
    return GanttProblem(
        name="task_pricing_service",
        tasks=(
            Task(
                task_key="t1",
                name="Task 1",
                duration=1.0,
                resource_requirements=(("r1", 1.0),),
            ),
            Task(
                task_key="t2",
                name="Task 2",
                duration=1.0,
                resource_requirements=(("r2", 1.0),),
            ),
        ),
        resources=(
            Resource(resource_key="r1", name="R1", capacity=1.0),
            Resource(resource_key="r2", name="R2", capacity=1.0),
        ),
        time_horizon=10.0,
    )


def _make_service() -> TaskApplicationService:
    """构建任务应用服务。/ Build task application service."""
    solver = _SuccessfulSolver()
    task_ctx = TaskContext()
    resource_ctx = ResourceContext()
    return TaskApplicationService(
        solver=solver,
        task_context=task_ctx,
        resource_context=resource_ctx,
    )


@dataclass(frozen=True)
class _DualSolver:
    """Return a genuine constraint dual without inventing a native backend."""

    @property
    def name(self) -> str:
        return "dual-fixture"

    def solve(self, model: object, *, options: object = None) -> SolverOutput:
        del model, options
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            values=SolveValue(values={}),
            dual_values={"task_compilation_0": -7.25},
        )


@dataclass(frozen=True)
class _SuccessfulSolver:
    """Return an optimal fixture without pretending to solve the model."""

    @property
    def name(self) -> str:
        return "successful-fixture"

    def solve(self, model: object, *, options: object = None) -> SolverOutput:
        del model, options
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            values=SolveValue(values={}),
        )


@dataclass
class _UnexpectedSolver:
    """Fail if the default solver path is used."""

    calls: list[object]

    @property
    def name(self) -> str:
        return "unexpected-fixture"

    def solve(self, model: object, *, options: object = None) -> SolverOutput:
        self.calls.append(model)
        return SolverOutput(status=SolverStatus.OPTIMAL)


class _StaticNativeModel:
    """Return one report while recording native solve arguments."""

    def __init__(self, report: SimpleNamespace) -> None:
        self.report = report
        self.calls: list[dict[str, object]] = []

    def solve_compiled(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return Ok(SimpleNamespace(report=self.report))


def _solve_report(
    *,
    termination_reason: str = "COMPLETED",
    problem_status: str = "FEASIBLE",
    solution_presence: str = "OPTIMAL",
    objective: float | None = 0.0,
    values: tuple[float, ...] = (),
) -> SimpleNamespace:
    """Build the minimal native report shape consumed by extraction."""
    return SimpleNamespace(
        termination_reason=termination_reason,
        problem_status=problem_status,
        solution_presence=solution_presence,
        objective=objective,
        values=values,
    )


def _make_large_native_service() -> tuple[TaskApplicationService, _UnexpectedSolver]:
    """Build a sufficiently large final MIP to observe real backend stops."""
    solver = _UnexpectedSolver([])
    service = TaskApplicationService(
        solver=solver,
        task_context=TaskContext(),
        resource_context=ResourceContext(),
        native_solver="gurobi10",
    )
    tasks = tuple(
        Task(
            task_key=f"t{index}",
            name=f"T{index}",
            duration=1.0,
            resource_requirements=(("r1", 1.0),),
        )
        for index in range(1000)
    )
    problem = GanttProblem(
        name="large_final_mip",
        tasks=tasks,
        resources=(Resource(resource_key="r1", name="R1", capacity=1000.0),),
        time_horizon=1001.0,
    )
    column = TaskColumn(
        "all",
        tuple((task.task_key, "r1", 0.0) for task in tasks),
        1000.0,
    )
    assert service.register(problem).is_ok()
    assert service.add_columns((column,)).is_ok()
    return service, solver


def _complete_column() -> TaskColumn:
    """Build one column covering every task in the fixture problem."""
    return TaskColumn(
        column_key="complete",
        task_assignments=(
            ("t1", "r1", 0.0),
            ("t2", "r1", 3.0),
            ("t3", "r1", 5.0),
        ),
        cost=10.0,
    )


def _cancel_after_native_build(
    monkeypatch: pytest.MonkeyPatch,
    scope: CancellationScope,
) -> list[MetaModelFloat64]:
    """Cancel after a real candidate build and retain it for close checks."""
    original = _task_application_service_module._build_native_task_model
    built: list[MetaModelFloat64] = []

    def build_then_cancel(**kwargs: object) -> object:
        result = original(**kwargs)  # type: ignore[arg-type]
        if result.is_ok():
            candidate = result.unwrap()
            built.append(candidate)
            assert scope.cancel(reason="after build").unwrap()
        return result

    monkeypatch.setattr(
        _task_application_service_module,
        "_build_native_task_model",
        build_then_cancel,
    )
    return built


# ==================== register 测试 / register tests ===========


class TestTaskRegister:
    """register 方法测试。/ register method tests."""

    def test_register_valid_problem_returns_ok(self) -> None:
        """有效问题注册返回 Ok。/ Valid problem register returns Ok."""
        service = _make_service()
        result = service.register(_make_problem())
        assert result.is_ok()

    def test_register_empty_tasks_returns_failed(self) -> None:
        """无任务问题注册返回失败。/ Empty tasks register fails."""
        service = _make_service()
        problem = GanttProblem(name="empty", tasks=(), resources=())
        result = service.register(problem)
        assert result.is_failed()

    def test_register_duplicate_tasks_returns_failed(self) -> None:
        """重复任务键注册返回失败。/ Duplicate task keys fail."""
        service = _make_service()
        tasks = (
            Task(task_key="t1", name="A", duration=1.0),
            Task(task_key="t1", name="B", duration=2.0),
        )
        resources = (Resource(resource_key="r1", name="R1", capacity=5.0),)
        problem = GanttProblem(name="dup", tasks=tasks, resources=resources)
        result = service.register(problem)
        assert result.is_failed()

    def test_register_sets_iteration_zero(self) -> None:
        """注册后迭代次数为 0。/ Iteration is 0 after register."""
        service = _make_service()
        service.register(_make_problem())
        assert service.iteration == 0

    def test_register_sets_converged_false(self) -> None:
        """注册后未收敛。/ Not converged after register."""
        service = _make_service()
        service.register(_make_problem())
        assert service.converged is False

    def test_register_clears_previous_state(self) -> None:
        """注册清除之前的状态。/ Register clears previous state."""
        service = _make_service()
        service.register(_make_problem())
        assert service.active_columns == ()
        assert service.shadow_prices == {}

    def test_register_with_precedence_relation(self) -> None:
        """带优先关系注册成功。/ Register with precedence succeeds."""
        service = _make_service()
        problem = _make_problem()
        result = service.register(problem)
        assert result.is_ok()

    def test_register_adds_task_compilation_rows_and_links(self) -> None:
        """注册任务编译等式和开始/分配桥。"""
        service = _make_service()
        assert service.register(_make_problem()).is_ok()
        native_model = service._native_model
        assert native_model is not None
        exported = native_model.to_linear_triad().unwrap()
        rows = {row.name: row for row in exported.rows}
        variables = {variable.name: variable for variable in exported.variables}

        assert rows["task_compilation_0"].rhs == 1.0
        assert rows["task_compilation_0"].relation == "=="
        assert rows["start_link_t1"].relation == "=="
        assert rows["assign_link_t1_r1"].relation == "=="
        assert variables["makespan"].kind == "continuous"

    def test_register_pre_cancelled_scope_preserves_published_state(self) -> None:
        """预取消注册不替换已有模型或列生成状态。"""
        service = _make_service()
        problem = _make_problem()
        seed = _complete_column()
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        assert service.refresh_shadow_price().is_ok()
        service._converged = True
        service._finite_pool_exhausted = True
        native_model = service._native_model
        prices = service.shadow_prices
        iteration = service.iteration
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.register(problem, cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service._problem is problem
        assert service.active_columns == (seed,)
        assert service.shadow_prices == prices
        assert service.iteration == iteration
        assert service.converged
        assert service.finite_pool_exhausted

    def test_register_cancel_after_build_closes_candidate_and_preserves_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """构建后取消关闭未发布候选并保留当前权威模型。"""
        service = _make_service()
        problem = _make_problem()
        seed = _complete_column()
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        built = _cancel_after_native_build(monkeypatch, scope)

        result = service.register(problem, cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert len(built) == 1
        assert built[0].to_linear_triad().is_failed()
        assert service._native_model is native_model
        assert service._problem is problem
        assert service.active_columns == (seed,)


# ==================== add_columns 测试 / add_columns tests =====


class TestTaskAddColumns:
    """add_columns 方法测试。/ add_columns method tests."""

    def test_add_columns_empty_returns_ok(self) -> None:
        """空列添加返回 Ok。/ Empty add returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        result = service.add_columns(())
        assert result.is_ok()

    def test_add_columns_before_register_returns_failed(self) -> None:
        """未注册时添加列返回失败。/ Add before register fails."""
        service = _make_service()
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        result = service.add_columns((col,))
        assert result.is_failed()

    def test_add_columns_new_column_returns_ok(self) -> None:
        """添加新列返回 Ok。/ Adding new column returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        result = service.add_columns((col,))
        assert result.is_ok()

    def test_add_columns_checks_resources_against_the_task(self) -> None:
        """未知资源或任务未声明资源时拒绝，未声明需求的旧任务保持兼容。"""
        service = _make_service()
        problem = GanttProblem(
            name="resource_validation",
            tasks=(
                Task("declared", "Declared", 3.0, resource_requirements=(("r1", 1.0),)),
                Task("wildcard", "Wildcard", 3.0),
            ),
            resources=(Resource("r1", "R1", 10.0), Resource("r2", "R2", 10.0)),
            time_horizon=20.0,
        )
        assert service.register(problem).is_ok()

        unknown = TaskColumn("unknown", (("declared", "missing", 0.0),), 5.0)
        assert service.add_columns((unknown,)).is_failed()

        mismatch = TaskColumn("mismatch", (("declared", "r2", 0.0),), 5.0)
        assert service.add_columns((mismatch,)).is_failed()

        wildcard = TaskColumn("wildcard", (("wildcard", "r2", 0.0),), 5.0)
        assert service.add_columns((wildcard,)).is_ok()

    def test_add_columns_updates_active_columns(self) -> None:
        """添加列后活跃列更新。/ Active columns updated after add."""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(
                ("t1", "r1", 0.0),
                ("t2", "r1", 3.0),
            ),
            cost=10.0,
        )
        service.add_columns((col,))
        assert len(service.active_columns) == 1
        assert service.active_columns[0].column_key == "c1"

    def test_add_columns_duplicate_returns_failed(self) -> None:
        """重复列添加返回失败。/ Duplicate column add fails."""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        service.add_columns((col,))
        result = service.add_columns((col,))
        assert result.is_failed()

    def test_failed_batch_preserves_the_native_model(self) -> None:
        """失败批次不替换已发布的 Rust 模型。"""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        assert service.add_columns((col,)).is_ok()
        native_model = service._native_model
        assert native_model is not None
        identity = native_model.model_identity

        assert service.add_columns((col,)).is_failed()

        assert service._native_model is native_model
        assert native_model.model_identity == identity
        assert service.active_columns == (col,)

    def test_add_multiple_columns(self) -> None:
        """添加多列成功。/ Adding multiple columns succeeds."""
        service = _make_service()
        service.register(_make_problem())
        cols = (
            TaskColumn(
                column_key="c1",
                task_assignments=(("t1", "r1", 0.0),),
                cost=5.0,
            ),
            TaskColumn(
                column_key="c2",
                task_assignments=(("t2", "r1", 3.0),),
                cost=4.0,
            ),
        )
        result = service.add_columns(cols)
        assert result.is_ok()
        assert len(service.active_columns) == 2

    def test_add_pre_cancelled_scope_preserves_published_state(self) -> None:
        """预取消加列不发布候选模型或清除价格状态。"""
        service = _make_service()
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        assert service.refresh_shadow_price().is_ok()
        service._converged = True
        service._finite_pool_exhausted = True
        native_model = service._native_model
        prices = service.shadow_prices
        iteration = service.iteration
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.add_columns(
            (TaskColumn("next", (("t1", "r1", 0.0),), 1.0),),
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert service.shadow_prices == prices
        assert service.iteration == iteration
        assert service.converged
        assert service.finite_pool_exhausted

    def test_add_cancel_after_build_closes_candidate_and_preserves_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """加列候选构建后取消关闭候选并保留已发布状态。"""
        service = _make_service()
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        built = _cancel_after_native_build(monkeypatch, scope)

        result = service.add_columns(
            (TaskColumn("next", (("t1", "r1", 0.0),), 1.0),),
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert len(built) == 1
        assert built[0].to_linear_triad().is_failed()
        assert service._native_model is native_model
        assert service.active_columns == (seed,)

    def test_add_observes_cancellation_inside_validation_loop(self) -> None:
        """批量校验循环在列内任务检查点响应取消。"""

        class _CancelOnThirdCheck(CancellationScope):
            __slots__ = ("checks",)

            def __init__(self) -> None:
                super().__init__()
                self.checks = 0

            @property
            def is_cancelled(self) -> bool:
                self.checks += 1
                return self.checks >= 3

        service = _make_service()
        assert service.register(_make_problem()).is_ok()
        native_model = service._native_model
        scope = _CancelOnThirdCheck()

        result = service.add_columns(
            (TaskColumn("next", (("t1", "r1", 0.0),), 1.0),),
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == ()

    def test_add_rejects_invalid_cancellation_before_mutation(self) -> None:
        """非法取消参数在模型变更前返回结构化错误。"""
        service = _make_service()
        assert service.register(_make_problem()).is_ok()
        native_model = service._native_model

        result = service.add_columns(
            (TaskColumn("next", (("t1", "r1", 0.0),), 1.0),),
            cancellation=object(),  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert service._native_model is native_model
        assert service.active_columns == ()


# ==================== remove_columns 测试 ========================


class TestTaskRemoveColumns:
    """remove_columns 方法测试。/ remove_columns method tests."""

    def test_remove_empty_returns_ok(self) -> None:
        """空移除返回 Ok。/ Empty remove returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        result = service.remove_columns(())
        assert result.is_ok()

    def test_remove_before_register_returns_failed(self) -> None:
        """未注册时移除返回失败。/ Remove before register fails."""
        service = _make_service()
        result = service.remove_columns(("c1",))
        assert result.is_failed()

    def test_remove_existing_column_returns_ok(self) -> None:
        """移除已存在列返回 Ok。/ Remove existing column returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        service.add_columns((col,))
        result = service.remove_columns(("c1",))
        assert result.is_ok()

    def test_remove_existing_column_removes_from_active(self) -> None:
        """移除后活跃列减少。/ Active columns decrease after remove."""
        service = _make_service()
        service.register(_make_problem())
        col1 = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        col2 = TaskColumn(
            column_key="c2",
            task_assignments=(("t2", "r1", 3.0),),
            cost=4.0,
        )
        service.add_columns((col1, col2))
        assert len(service.active_columns) == 2
        service.remove_columns(("c1",))
        assert len(service.active_columns) == 1
        assert service.active_columns[0].column_key == "c2"

    def test_remove_rebuilds_the_native_model_atomically(self) -> None:
        """删除列后发布新的原生模型，旧身份不再作为当前权威。"""
        service = _make_service()
        service.register(_make_problem())
        col = TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        )
        assert service.add_columns((col,)).is_ok()
        before = service._native_model
        assert before is not None

        assert service.remove_columns(("c1",)).is_ok()

        assert service._native_model is not None
        assert service._native_model is not before
        assert before.to_linear_triad().is_failed()
        assert service.active_columns == ()

    def test_remove_pre_cancelled_scope_preserves_published_state(self) -> None:
        """预取消删列不重建或清除已发布状态。"""
        service = _make_service()
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        assert service.refresh_shadow_price().is_ok()
        service._converged = True
        service._finite_pool_exhausted = True
        native_model = service._native_model
        prices = service.shadow_prices
        iteration = service.iteration
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.remove_columns(("complete",), cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert service.shadow_prices == prices
        assert service.iteration == iteration
        assert service.converged
        assert service.finite_pool_exhausted

    def test_remove_cancel_after_build_closes_candidate_and_preserves_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """删列候选构建后取消关闭候选并保留原活跃列。"""
        service = _make_service()
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        built = _cancel_after_native_build(monkeypatch, scope)

        result = service.remove_columns(("complete",), cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert len(built) == 1
        assert built[0].to_linear_triad().is_failed()
        assert service._native_model is native_model
        assert service.active_columns == (seed,)


# ==================== refresh_shadow_price 测试 =================


class TestTaskRefreshShadowPrice:
    """refresh_shadow_price 方法测试。/ refresh_shadow_price tests."""

    def test_refresh_before_register_returns_failed(self) -> None:
        """未注册时刷新返回失败。/ Refresh before register fails."""
        service = _make_service()
        result = service.refresh_shadow_price()
        assert result.is_failed()

    def test_refresh_after_register_returns_ok(self) -> None:
        """注册后刷新返回 Ok。/ Refresh after register returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        result = service.refresh_shadow_price()
        assert result.is_ok()

    def test_refresh_returns_shadow_prices_dict(self) -> None:
        """刷新返回影子价格字典。/ Refresh returns shadow prices."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        result = service.refresh_shadow_price()
        prices = result.unwrap()
        assert isinstance(prices, dict)

    def test_refresh_forwards_solver_duals_to_native_task_algorithm(self) -> None:
        """求解器对偶进入固定算法，不回落为紧约束标记。 /
        Solver duals reach the pinned algorithm instead of tightness flags.
        """
        service = TaskApplicationService(
            solver=_DualSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert service.register(_make_problem()).is_ok()

        prices = service.refresh_shadow_price().unwrap()

        assert prices == {"task_compilation_0": -7.25}

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_refresh_uses_certified_native_lp_dual_without_default_solver(self) -> None:
        """显式原生标记使用松弛证书价格，不调用 fixture solver。 /
        An explicit native marker uses certified relaxed prices and skips the fixture solver.
        """
        calls: list[object] = []
        service = TaskApplicationService(
            solver=_UnexpectedSolver(calls),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="native_lp",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        assert service.register(problem).is_ok()
        assert service.add_columns(
            (TaskColumn("c", (("t1", "r1", 0.0),), 2.5),)
        ).is_ok()

        prices = service.refresh_shadow_price().unwrap()

        assert prices == {"task_compilation_0": 2.5}
        assert calls == []

    def test_refresh_stop_controls_require_an_explicit_native_backend(self) -> None:
        """默认求解器路径不得静默忽略影子价格停止参数。"""
        calls: list[object] = []
        service = TaskApplicationService(
            solver=_UnexpectedSolver(calls),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((_complete_column(),)).is_ok()

        results = (
            service.refresh_shadow_price(time_limit=1.0),
            service.refresh_shadow_price(cancellation=CancellationScope()),
            service.refresh_shadow_price(on_progress=lambda _: None),
        )

        assert all(result.is_failed() for result in results)
        assert all(result.error.code is ErrorCode.NOT_SUPPORTED for result in results)
        assert calls == []
        assert service.iteration == 0
        assert service.shadow_prices == {}

    @pytest.mark.parametrize(
        "controls",
        (
            {"time_limit": True},
            {"time_limit": 0},
            {"time_limit": float("inf")},
            {"time_limit": float("nan")},
            {"time_limit": 2**53},
            {"cancellation": object()},
            {"on_progress": 123},
        ),
    )
    def test_refresh_rejects_invalid_stop_controls(
        self,
        controls: dict[str, object],
    ) -> None:
        """非法停止参数在模型导出前返回结构化错误。"""
        result = _make_service().refresh_shadow_price(**controls)  # type: ignore[arg-type]

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT

    def test_refresh_pre_cancelled_scope_preserves_published_state(self) -> None:
        """预取消原生影子价格刷新不导出或修改当前模型。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.refresh_shadow_price(cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert service.iteration == 0
        assert service.shadow_prices == {}

    def test_refresh_forwards_native_stop_controls(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """公共刷新入口把已校验停止控制传给原生 LP attempt。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((_complete_column(),)).is_ok()
        scope = CancellationScope()

        def on_progress(_: object) -> None:
            return None

        calls: list[dict[str, object]] = []

        def refresh(**kwargs: object) -> object:
            calls.append(kwargs)
            return Ok({"task_compilation_0": 2.5})

        monkeypatch.setattr(service, "_refresh_native_shadow_price", refresh)

        result = service.refresh_shadow_price(
            time_limit=2,
            cancellation=scope,
            on_progress=on_progress,
        )

        assert result.unwrap() == {"task_compilation_0": 2.5}
        assert calls == [
            {
                "time_limit": 2.0,
                "cancellation": scope,
                "on_progress": on_progress,
            }
        ]

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_refresh_public_stop_controls_use_native_lp_without_fixture_solver(
        self,
    ) -> None:
        """真实 Gurobi 10 公共刷新接受时限、作用域和进度回调。"""
        calls: list[object] = []
        service = TaskApplicationService(
            solver=_UnexpectedSolver(calls),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="native_lp_stop_controls",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        assert service.register(problem).is_ok()
        assert service.add_columns(
            (TaskColumn("c", (("t1", "r1", 0.0),), 2.5),)
        ).is_ok()

        prices = service.refresh_shadow_price(
            time_limit=5.0,
            cancellation=CancellationScope(),
            on_progress=lambda _: None,
        ).unwrap()

        assert prices == {"task_compilation_0": 2.5}
        assert calls == []

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_refresh_native_callback_cancel_preserves_state(self) -> None:
        """公共刷新在原生回调取消时返回 CANCELLED 且不发布价格。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="native_lp_callback_cancel",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        assert service.register(problem).is_ok()
        assert service.add_columns(
            (TaskColumn("c", (("t1", "r1", 0.0),), 2.5),)
        ).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        progress_events: list[object] = []

        def cancel(event: _native.SolveProgress) -> None:
            if event.stage == "solving" and not scope.is_cancelled:
                progress_events.append(event)
                assert scope.cancel(reason="LP callback").unwrap()

        result = service.refresh_shadow_price(
            cancellation=scope,
            on_progress=cancel,
        )

        assert progress_events
        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.iteration == 0
        assert service.shadow_prices == {}

    def test_refresh_increments_iteration(self) -> None:
        """刷新后迭代次数增加。/ Iteration increments after refresh."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        assert service.iteration == 0
        service.refresh_shadow_price()
        assert service.iteration == 1

    def test_refresh_converges_at_max_iterations(self) -> None:
        """达到最大迭代时收敛。/ Converges at max iterations."""
        service = _make_service()
        service._max_iterations = 2
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        service.refresh_shadow_price()
        assert service.converged is False
        service.refresh_shadow_price()
        assert service.converged is True


# ==================== run_task_pricing 测试 =======================


class TestTaskRunTaskPricing:
    """显式无时隙任务定价服务入口测试 / Explicit unslotted task-pricing service tests."""

    def test_requires_a_registered_problem(self) -> None:
        service = _make_service()

        result = service.run_task_pricing(
            columns=(),
            policy=lambda _: {},
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.NOT_INITIALIZED

    def test_requires_an_explicit_native_backend(self) -> None:
        service = _make_service()
        assert service.register(_make_pricing_problem()).is_ok()
        native_model = service._native_model

        result = service.run_task_pricing(
            columns=(),
            policy=lambda _: {},
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.NOT_SUPPORTED
        assert service._native_model is native_model
        assert service.active_columns == ()

    def test_invalid_time_limit_preserves_the_gantt_state(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_pricing_problem()).is_ok()
        native_model = service._native_model

        result = service.run_task_pricing(
            columns=(),
            policy=lambda _: {},
            time_limit=0,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert service._native_model is native_model
        assert service.active_columns == ()
        assert service.iteration == 0

    def test_rejects_a_resource_not_required_by_the_task(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_pricing_problem()).is_ok()

        result = service.run_task_pricing(
            columns=((0, 1, 1.0),),
            policy=lambda _: {},
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.NOT_FOUND
        assert service.active_columns == ()

    def test_pre_cancelled_scope_preserves_the_gantt_state(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_pricing_problem()).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.run_task_pricing(
            columns=(),
            policy=lambda _: {},
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == ()
        assert service.iteration == 0

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_service_consumes_the_public_facade_without_mutating_gantt_state(
        self,
    ) -> None:
        solver = _UnexpectedSolver([])
        service = TaskApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = _make_pricing_problem()
        assert service.register(problem).is_ok()
        native_model = service._native_model
        seen: dict[str, Any] = {}

        def policy(request: dict[str, Any]) -> dict[str, Any]:
            seen.update(request)
            return {
                "columns": [],
                "completion": "EXHAUSTED",
                "no_improving_columns": True,
            }

        result = service.run_task_pricing(
            columns=((0, 0, 1.0), (1, 1, 2.0)),
            policy=policy,
        ).unwrap()

        assert result.task_keys == ("t1", "t2")
        assert result.resource_keys == ("r1", "r2")
        assert result.lp_report.is_optimal
        assert result.lp_report.objective == pytest.approx(3.0)
        assert result.batch.columns == []
        assert result.batch.completion == "EXHAUSTED"
        assert result.batch.global_scope
        assert result.batch.no_improving_columns is True
        assert result.certified_lower_bound == pytest.approx(3.0)
        assert seen["verified_duals"] is True
        assert seen["tasks"] == [0, 1]
        assert solver.calls == []
        assert service._native_model is native_model
        assert service.active_columns == ()
        assert service.shadow_prices == {}
        assert service.iteration == 0
        assert service.converged is False

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_rejects_incompatible_policy_columns_without_mutating_gantt_state(
        self,
    ) -> None:
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_pricing_problem()).is_ok()
        native_model = service._native_model

        result = service.run_task_pricing(
            columns=((0, 0, 1.0), (1, 1, 2.0)),
            policy=lambda _: {
                "columns": [(0, 1, 0.5)],
                "completion": "HEURISTIC",
                "no_improving_columns": False,
            },
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.NOT_FOUND
        assert service._native_model is native_model
        assert service.active_columns == ()
        assert service.shadow_prices == {}
        assert service.iteration == 0
        assert service.converged is False


# ==================== run_column_generation 测试 ===============


class TestTaskRunColumnGeneration:
    """有限候选池自动列生成测试 / Finite-pool automatic column-generation tests."""

    def test_run_requires_an_explicit_native_backend(self) -> None:
        service = _make_service()
        assert service.register(_make_problem()).is_ok()

        result = service.run_column_generation(candidates=())

        assert result.is_failed()

    def test_run_requires_a_seed_column(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_problem()).is_ok()

        result = service.run_column_generation(candidates=())

        assert result.is_failed()

    def test_invalid_candidate_preserves_the_published_model(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_problem()).is_ok()
        seed = _complete_column()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None

        result = service.run_column_generation(
            candidates=(
                seed,
                TaskColumn("bad", (("missing", "r1", 0.0),), 0.0),
            )
        )

        assert result.is_failed()
        assert service._native_model is native_model
        assert service.active_columns == (seed,)

    def test_pre_cancelled_scope_preserves_the_published_model(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="pre_cancelled",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        cheap = TaskColumn("cheap", (("t1", "r1", 0.0),), 1.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.run_column_generation(
            candidates=(seed, cheap),
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert not service.converged
        assert not service.finite_pool_exhausted

    def test_invalid_cancellation_preserves_the_published_model(self) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="invalid_cancellation",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None

        result = service.run_column_generation(
            candidates=(seed,),
            cancellation=object(),  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert service._native_model is native_model
        assert service.active_columns == (seed,)

    @pytest.mark.parametrize(
        "time_limit",
        (True, 0, -1.0, float("inf"), float("nan"), 2**53),
    )
    def test_invalid_time_limit_preserves_the_published_model(
        self, time_limit: object
    ) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="invalid_time_limit",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None

        result = service.run_column_generation(
            candidates=(seed,),
            time_limit=time_limit,  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert service._native_model is native_model
        assert service.active_columns == (seed,)

    def test_expired_time_limit_preserves_the_published_model(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="expired_time_limit",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None
        ticks = iter((0.0, 2.0))
        monkeypatch.setattr(
            _task_application_service_module.time,
            "monotonic",
            lambda: next(ticks),
        )

        result = service.run_column_generation(
            candidates=(seed,),
            time_limit=1.0,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.TIMEOUT
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert not service.converged
        assert not service.finite_pool_exhausted

    def test_termination_reasons_map_to_structured_stops(self) -> None:
        cancelled = _task_application_service_module._termination_failure("CANCELLED")
        timeout = _task_application_service_module._termination_failure("TIME_LIMIT")
        failed = _task_application_service_module._termination_failure("ERROR")

        assert cancelled.is_failed()
        assert cancelled.error.code is ErrorCode.CANCELLED
        assert timeout.is_failed()
        assert timeout.error.code is ErrorCode.TIMEOUT
        assert failed.is_failed()
        assert failed.error.code is ErrorCode.SOLVE_FAILED

    def test_native_stop_preserves_the_published_model_and_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="native_stop",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        cheap = TaskColumn("cheap", (("t1", "r1", 0.0),), 1.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        assert native_model is not None
        monkeypatch.setattr(
            service,
            "_refresh_native_shadow_price",
            lambda **_: _task_application_service_module._timeout_failure(),
        )

        result = service.run_column_generation(candidates=(seed, cheap))

        assert result.is_failed()
        assert result.error.code is ErrorCode.TIMEOUT
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert not service.converged
        assert not service.finite_pool_exhausted

    def test_cancelled_scope_takes_priority_over_native_failure(self) -> None:
        scope = CancellationScope()

        class _CancellingFailedModel:
            def to_linear_triad(self) -> object:
                return Ok(object())

            def solve_relaxed_compiled(self, **_: object) -> object:
                assert scope.cancel(reason="native failure").unwrap()
                return Failed(
                    ExErr(
                        _code=ErrorCode.SOLVE_FAILED,
                        _message="native failure",
                        value={},
                    )
                )

        service = TaskApplicationService(
            solver=_SuccessfulSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )

        result = service._refresh_native_shadow_price(
            model=_CancellingFailedModel(),  # type: ignore[arg-type]
            cancellation=scope,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_scope_cancels_the_second_attempt_without_losing_published_columns(
        self,
    ) -> None:
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="second_attempt_cancel",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        cheap = TaskColumn("cheap", (("t1", "r1", 0.0),), 1.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()
        scope = CancellationScope()
        first_attempt: int | None = None

        def cancel_second(event: _native.SolveProgress) -> None:
            nonlocal first_attempt
            attempt = event.attempt_identity
            if first_attempt is None:
                first_attempt = attempt
            elif attempt != first_attempt and not scope.is_cancelled:
                assert scope.cancel(reason="second attempt").unwrap()

        result = service.run_column_generation(
            candidates=(seed, cheap),
            cancellation=scope,
            on_progress=cancel_second,
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service.active_columns == (seed, cheap)
        assert not service.converged
        assert not service.finite_pool_exhausted

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_finite_pool_adds_only_strictly_improving_columns(self) -> None:
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = GanttProblem(
            name="finite_pool",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        cheap = TaskColumn("cheap", (("t1", "r1", 0.0),), 1.5)
        expensive = TaskColumn("expensive", (("t1", "r1", 0.0),), 2.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()

        added = service.run_column_generation(
            candidates=(seed, cheap, expensive)
        ).unwrap()

        assert added == (cheap,)
        assert service.active_columns == (seed, cheap)
        assert service.finite_pool_exhausted
        assert service.converged

        solution = service.extract_solution().unwrap()
        assert solution.is_optimal
        assert solution.makespan == pytest.approx(3.0)
        assert solution.objective_value == pytest.approx(4.5)

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_iteration_limit_does_not_claim_finite_pool_exhaustion(self) -> None:
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
            max_iterations=1,
        )
        problem = GanttProblem(
            name="finite_pool_limit",
            tasks=(Task("t1", "T1", 3.0, resource_requirements=(("r1", 1.0),)),),
            resources=(Resource("r1", "R1", 10.0),),
            time_horizon=20.0,
        )
        seed = TaskColumn("seed", (("t1", "r1", 0.0),), 2.5)
        cheap = TaskColumn("cheap", (("t1", "r1", 0.0),), 1.5)
        assert service.register(problem).is_ok()
        assert service.add_columns((seed,)).is_ok()

        added = service.run_column_generation(candidates=(seed, cheap)).unwrap()

        assert added == (cheap,)
        assert not service.finite_pool_exhausted
        assert service.converged


# ==================== finalize 测试 / finalize tests =============


class TestTaskFinalize:
    """finalize 方法测试。/ finalize method tests."""

    def test_finalize_before_register_returns_failed(self) -> None:
        """未注册时终止返回失败。/ Finalize before register fails."""
        service = _make_service()
        result = service.finalize()
        assert result.is_failed()

    def test_finalize_after_register_returns_ok(self) -> None:
        """注册后终止返回 Ok。/ Finalize after register returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        result = service.finalize()
        assert result.is_ok()

    def test_finalize_sets_converged(self) -> None:
        """终止后设置收敛标志。/ Finalize sets converged flag."""
        service = _make_service()
        service.register(_make_problem())
        service.finalize()
        assert service.converged is True


# ==================== extract_solution 测试 ======================


class TestTaskExtractSolution:
    """extract_solution 方法测试。/ extract_solution tests."""

    def test_extract_before_register_returns_failed(self) -> None:
        """未注册时提取返回失败。/ Extract before register fails."""
        service = _make_service()
        result = service.extract_solution()
        assert result.is_failed()

    def test_extract_after_register_returns_ok(self) -> None:
        """完整列注册后提取返回 Ok。/ Extract after complete columns returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        result = service.extract_solution()
        assert result.is_ok()

    def test_extract_without_columns_is_infeasible(self) -> None:
        """空初始列集不能被伪装成可行解。"""
        service = TaskApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert service.register(_make_problem()).is_ok()
        assert service.extract_solution().is_failed()

    def test_extract_produces_solution_name(self) -> None:
        """提取的方案包含名称。/ Extracted solution has name."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        solution = service.extract_solution().unwrap()
        assert "task_test" in solution.name

    def test_extract_produces_schedule_entries(self) -> None:
        """提取的方案包含调度条目。/ Solution has schedule entries."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        solution = service.extract_solution().unwrap()
        assert solution.task_count == 3

    def test_extract_makespan_is_nonnegative(self) -> None:
        """完工时间为非负。/ Makespan is nonnegative."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        solution = service.extract_solution().unwrap()
        assert solution.makespan >= 0.0

    def test_extract_with_columns_returns_schedule(self) -> None:
        """有列时提取返回调度。/ Extract with columns returns schedule."""
        service = _make_service()
        service.register(_make_problem())
        assert service.add_columns((_complete_column(),)).is_ok()
        result = service.extract_solution()
        assert result.is_ok()

    def test_extract_stop_controls_require_an_explicit_native_backend(self) -> None:
        """默认求解器路径不得静默忽略停止参数。"""
        calls: list[object] = []
        service = TaskApplicationService(
            solver=_UnexpectedSolver(calls),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((_complete_column(),)).is_ok()

        results = (
            service.extract_solution(time_limit=1.0),
            service.extract_solution(cancellation=CancellationScope()),
            service.extract_solution(on_progress=lambda _: None),
        )

        assert all(result.is_failed() for result in results)
        assert all(result.error.code is ErrorCode.NOT_SUPPORTED for result in results)
        assert calls == []

    def test_extract_native_with_active_columns_uses_finite_activity_bridge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """显式原生后端和活跃列应走 Rust activity 有限列桥。"""
        solver = _UnexpectedSolver([])
        service = TaskApplicationService(
            solver=solver,
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        problem = _make_problem()
        scope = CancellationScope()
        events: list[object] = []
        on_progress = events.append
        expected = GanttSolution(name="finite activity bridge")
        calls: list[dict[str, object]] = []

        def solve_finite(**kwargs: object) -> Ok[GanttSolution]:
            calls.append(kwargs)
            return Ok(expected)

        monkeypatch.setattr(service, "_problem", problem)
        monkeypatch.setattr(service, "_native_model", object())
        monkeypatch.setattr(service, "_active_columns", [_complete_column()])
        monkeypatch.setattr(service, "_extract_finite_task_solution", solve_finite)

        result = service.extract_solution(
            time_limit=1.0,
            cancellation=scope,
            on_progress=on_progress,
        )

        assert result.unwrap() is expected
        assert calls == [
            {
                "solver": "gurobi10",
                "time_limit": 1.0,
                "cancellation": scope,
                "on_progress": on_progress,
            }
        ]
        assert solver.calls == []

    @pytest.mark.parametrize(
        "time_limit",
        (True, 0, -1.0, float("inf"), float("nan"), 2**53),
    )
    def test_extract_rejects_invalid_time_limit(self, time_limit: object) -> None:
        """非法时限在进入模型前返回结构化错误。"""
        result = _make_service().extract_solution(
            time_limit=time_limit,  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT

    def test_extract_rejects_invalid_cancellation(self) -> None:
        """取消参数必须是 CancellationScope。"""
        result = _make_service().extract_solution(
            cancellation=object(),  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT

    def test_extract_rejects_invalid_progress_callback(self) -> None:
        """进度回调必须可调用。"""
        result = _make_service().extract_solution(
            on_progress=123,  # type: ignore[arg-type]
        )

        assert result.is_failed()
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT

    def test_extract_pre_cancelled_scope_preserves_published_state(self) -> None:
        """预取消在导出求解快照前停止且不改变已发布状态。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        seed = _complete_column()
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((seed,)).is_ok()
        native_model = service._native_model
        scope = CancellationScope()
        assert scope.cancel(reason="preflight").unwrap()

        result = service.extract_solution(cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert service._native_model is native_model
        assert service.active_columns == (seed,)
        assert not service.converged

    @pytest.mark.parametrize(
        ("report", "expected"),
        (
            (
                _solve_report(
                    termination_reason="CANCELLED",
                    solution_presence="FEASIBLE",
                    objective=19.0,
                    values=(0.0, 3.0, 5.0),
                ),
                ErrorCode.CANCELLED,
            ),
            (
                _solve_report(
                    termination_reason="TIME_LIMIT",
                    solution_presence="NONE",
                    objective=None,
                ),
                ErrorCode.TIMEOUT,
            ),
            (
                _solve_report(
                    termination_reason="COMPLETED",
                    solution_presence="NONE",
                    objective=None,
                ),
                ErrorCode.SOLVE_FAILED,
            ),
            (
                _solve_report(
                    termination_reason="ERROR",
                    solution_presence="NONE",
                    objective=None,
                ),
                ErrorCode.SOLVE_FAILED,
            ),
            (
                _solve_report(
                    problem_status="INFEASIBLE",
                    solution_presence="NONE",
                    objective=None,
                ),
                ErrorCode.NO_SOLUTION,
            ),
        ),
    )
    def test_extract_native_reports_map_to_structured_stops(
        self,
        monkeypatch: pytest.MonkeyPatch,
        report: SimpleNamespace,
        expected: ErrorCode,
    ) -> None:
        """原生终态映射为取消、超时、不可行或一般失败。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        monkeypatch.setattr(service, "_problem", _make_problem())
        monkeypatch.setattr(service, "_native_model", _StaticNativeModel(report))

        result = service._extract_native_solution(
            solver="gurobi10",
            triad=LinearTriadModel(),
        )

        assert result.is_failed()
        assert result.error.code is expected

    def test_extract_time_limit_feasible_returns_non_optimal_incumbent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """有时限的可行 incumbent 保留方案但不得宣称最优。"""
        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        report = _solve_report(
            termination_reason="TIME_LIMIT",
            solution_presence="FEASIBLE",
            objective=19.0,
            values=(0.0, 3.0, 5.0),
        )
        native_model = _StaticNativeModel(report)
        triad = LinearTriadModel(
            variables=["start_t1", "start_t2", "start_t3"],
        )
        scope = CancellationScope()
        events: list[object] = []
        on_progress = events.append
        monkeypatch.setattr(service, "_problem", _make_problem())
        monkeypatch.setattr(service, "_native_model", native_model)
        monkeypatch.setattr(
            service,
            "_native_triad",
            lambda *, relaxation: Ok(triad),
        )

        result = service.extract_solution(
            time_limit=1.0,
            cancellation=scope,
            on_progress=on_progress,
        )

        assert result.is_ok()
        solution = result.unwrap()
        assert not solution.is_optimal
        assert solution.makespan == pytest.approx(9.0)
        assert solution.objective_value == pytest.approx(19.0)
        assert native_model.calls[0]["time_limit"] == 1.0
        assert native_model.calls[0]["cancellation"] is not None
        assert native_model.calls[0]["on_progress"] is on_progress

    def test_cancelled_scope_takes_priority_over_final_native_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """原生失败且作用域已取消时优先返回 CANCELLED。"""
        scope = CancellationScope()

        class _CancellingFailedModel:
            def solve_compiled(self, **_: object) -> object:
                assert scope.cancel(reason="native failure").unwrap()
                return Failed(
                    ExErr(
                        _code=ErrorCode.SOLVE_FAILED,
                        _message="native failure",
                        value={},
                    )
                )

        service = TaskApplicationService(
            solver=_UnexpectedSolver([]),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        monkeypatch.setattr(service, "_problem", _make_problem())
        monkeypatch.setattr(service, "_native_model", _CancellingFailedModel())
        monkeypatch.setattr(
            service,
            "_native_triad",
            lambda *, relaxation: Ok(LinearTriadModel()),
        )

        result = service.extract_solution(cancellation=scope)

        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    @pytest.mark.timeout(30)
    def test_native_final_mip_time_limit_preserves_feasible_incumbent(
        self,
    ) -> None:
        """真实 Gurobi 10 最终 MIP 超时只发布合法结构化终态。"""
        service, solver = _make_large_native_service()

        result = service.extract_solution(time_limit=1e-5)

        if result.is_failed():
            assert result.error.code is ErrorCode.TIMEOUT
        else:
            solution = result.unwrap()
            assert not solution.is_optimal
            assert solution.makespan == pytest.approx(1.0)
        assert solver.calls == []

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    @pytest.mark.timeout(30)
    def test_native_final_mip_callback_cancels_with_cancelled_result(self) -> None:
        """真实 Gurobi 10 最终 MIP 回调取消映射为 CANCELLED。"""
        service, solver = _make_large_native_service()
        scope = CancellationScope()
        backend_events: list[object] = []

        def cancel(event: _native.SolveProgress) -> None:
            if event.source == "backend" and not scope.is_cancelled:
                backend_events.append(event)
                assert scope.cancel(reason="final MIP callback").unwrap()

        result = service.extract_solution(
            cancellation=scope,
            on_progress=cancel,
        )

        assert backend_events
        assert result.is_failed()
        assert result.error.code is ErrorCode.CANCELLED
        assert solver.calls == []

    @pytest.mark.skipif(
        "gurobi10" not in _native.build_info()["native_solvers"].split(","),
        reason="Rust gurobi10 backend not compiled",
    )
    def test_extract_uses_native_compiled_mip_without_fixture_solver(self) -> None:
        """显式原生标记直接提取最终 MIP，不调用 fixture solver。"""
        calls: list[object] = []
        service = TaskApplicationService(
            solver=_UnexpectedSolver(calls),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            native_solver="gurobi10",
        )
        assert service.register(_make_problem()).is_ok()
        assert service.add_columns((_complete_column(),)).is_ok()

        solution = service.extract_solution().unwrap()

        assert calls == []
        assert solution.is_optimal
        assert solution.makespan == pytest.approx(9.0)
        assert solution.objective_value == pytest.approx(19.0)
        assert [(entry.task_key, entry.start_time) for entry in solution.schedule] == [
            ("t1", 0.0),
            ("t2", 3.0),
            ("t3", 5.0),
        ]


class TestUtilizationCountsResourceAmounts:
    """利用率按资源量计算，不按任务条数 / Utilization counts resource amounts, not task counts."""

    def _service_with_problem(self) -> TaskApplicationService:
        """造一个两任务各需 3 单位 r1、容量 10 的服务。

        A service whose two tasks each require 3 units of r1, with capacity 10.
        """
        service = TaskApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        service._problem = GanttProblem(
            name="util",
            tasks=(
                TaskProblem(
                    task_key="t1", duration=3.0, resource_requirements=(("r1", 3.0),)
                ),
                TaskProblem(
                    task_key="t2", duration=2.0, resource_requirements=(("r1", 3.0),)
                ),
            ),
            resources=(Resource(resource_key="r1", name="R1", capacity=10.0),),
        )
        return service

    def test_used_capacity_sums_requirement_amounts(self) -> None:
        """两个各需 3.0 的任务必须占用 6.0，而不是 2 条任务。

        Two tasks requiring 3.0 each must occupy 6.0, not two tasks.
        """
        service = self._service_with_problem()
        schedule = (
            TaskScheduleEntry(
                task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"
            ),
            TaskScheduleEntry(
                task_key="t2", start_time=3.0, end_time=5.0, assigned_resource="r1"
            ),
        )
        (utilization,) = service._compute_utilizations(schedule=schedule, makespan=5.0)
        assert utilization.used_capacity == pytest.approx(6.0)
        assert utilization.utilization_rate == pytest.approx(0.6)
