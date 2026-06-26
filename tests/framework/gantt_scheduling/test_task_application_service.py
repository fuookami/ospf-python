"""任务应用服务测试 / Task application service tests.

覆盖 TaskApplicationService 的列生成生命周期方法。
Covers TaskApplicationService column generation lifecycle
methods.
"""

from __future__ import annotations

from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
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


def _make_problem() -> GanttProblem:
    """构建测试用甘特问题。/ Build test gantt problem."""
    tasks = (
        Task(
            task_key="t1", name="Task 1", duration=3.0,
            priority=1,
            resource_requirements=(("r1", 1.0),),
        ),
        Task(
            task_key="t2", name="Task 2", duration=2.0,
            priority=2,
            resource_requirements=(("r1", 1.0),),
        ),
        Task(
            task_key="t3", name="Task 3", duration=4.0,
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
                predecessor_key="t1", successor_key="t2",
            ),
        ),
        time_horizon=20.0,
    )


def _make_service() -> TaskApplicationService:
    """构建任务应用服务。/ Build task application service."""
    solver = MockSolver()
    task_ctx = TaskContext()
    resource_ctx = ResourceContext()
    return TaskApplicationService(
        solver=solver,
        task_context=task_ctx,
        resource_context=resource_ctx,
    )


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
        result = service.refresh_shadow_price()
        assert result.is_ok()

    def test_refresh_returns_shadow_prices_dict(self) -> None:
        """刷新返回影子价格字典。/ Refresh returns shadow prices."""
        service = _make_service()
        service.register(_make_problem())
        result = service.refresh_shadow_price()
        prices = result.unwrap()
        assert isinstance(prices, dict)

    def test_refresh_increments_iteration(self) -> None:
        """刷新后迭代次数增加。/ Iteration increments after refresh."""
        service = _make_service()
        service.register(_make_problem())
        assert service.iteration == 0
        service.refresh_shadow_price()
        assert service.iteration == 1

    def test_refresh_converges_at_max_iterations(self) -> None:
        """达到最大迭代时收敛。/ Converges at max iterations."""
        service = _make_service()
        service._max_iterations = 2
        service.register(_make_problem())
        service.refresh_shadow_price()
        assert service.converged is False
        service.refresh_shadow_price()
        assert service.converged is True


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
        """注册后提取返回 Ok。/ Extract after register returns Ok."""
        service = _make_service()
        service.register(_make_problem())
        result = service.extract_solution()
        assert result.is_ok()

    def test_extract_produces_solution_name(self) -> None:
        """提取的方案包含名称。/ Extracted solution has name."""
        service = _make_service()
        service.register(_make_problem())
        solution = service.extract_solution().unwrap()
        assert "task_test" in solution.name

    def test_extract_produces_schedule_entries(self) -> None:
        """提取的方案包含调度条目。/ Solution has schedule entries."""
        service = _make_service()
        service.register(_make_problem())
        solution = service.extract_solution().unwrap()
        assert solution.task_count == 3

    def test_extract_makespan_is_nonnegative(self) -> None:
        """完工时间为非负。/ Makespan is nonnegative."""
        service = _make_service()
        service.register(_make_problem())
        solution = service.extract_solution().unwrap()
        assert solution.makespan >= 0.0

    def test_extract_with_columns_returns_schedule(self) -> None:
        """有列时提取返回调度。/ Extract with columns returns schedule."""
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
        result = service.extract_solution()
        assert result.is_ok()
