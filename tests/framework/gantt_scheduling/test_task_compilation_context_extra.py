"""任务编译上下文额外测试 / Task compilation context extra tests.

补充覆盖 TaskCompilationContext 的注册、查询、容量和模型构建方法。
Supplementary coverage for TaskCompilationContext registration,
query, capacity, and model building methods.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.task_compilation.task_compilation_context import (
    TaskCompilationContext,
)

# ==================== 辅助数据类型 / Helper data types ===========


@dataclass(frozen=True)
class _FakeTask:
    """测试用任务。/ Test task."""
    task_key: str
    name: str = ""
    duration: float = 1.0
    priority: int = 0


@dataclass(frozen=True)
class _FakeAssignment:
    """测试用分配。/ Test assignment."""
    task_key: str
    resource_key: str
    name: str = "assignment"


@dataclass(frozen=True)
class _FakeCapacity:
    """测试用容量。/ Test capacity."""
    resource_key: str
    window_start: float
    window_end: float
    max_capacity: float
    name: str = "capacity"


@dataclass(frozen=True)
class _FakeLoad:
    """测试用负载。/ Test load."""
    resource_key: str
    load_amount: float
    name: str = "load"


# ==================== 注册测试 / Registration tests ==============


class TestTaskCompilationRegister:
    """注册方法测试。/ Registration method tests."""

    def test_register_task_returns_new_context(self) -> None:
        """注册任务返回新上下文。/ Register task returns new context."""
        ctx = TaskCompilationContext()
        task = _FakeTask(task_key="t1")
        new_ctx = ctx.register_task(task)
        assert new_ctx is not ctx

    def test_register_task_preserves_existing(self) -> None:
        """注册任务保留已有任务。/ Register task preserves existing."""
        ctx = TaskCompilationContext()
        t1 = _FakeTask(task_key="t1")
        t2 = _FakeTask(task_key="t2")
        ctx = ctx.register_task(t1)
        ctx = ctx.register_task(t2)
        assert len(ctx.get_all_tasks()) == 2

    def test_register_assignment_returns_new_context(self) -> None:
        """注册分配返回新上下文。/ Register assignment returns new context."""
        ctx = TaskCompilationContext()
        a = _FakeAssignment(task_key="t1", resource_key="r1")
        new_ctx = ctx.register_assignment(a)
        assert new_ctx is not ctx

    def test_register_capacity_returns_new_context(self) -> None:
        """注册容量返回新上下文。/ Register capacity returns new context."""
        ctx = TaskCompilationContext()
        cap = _FakeCapacity(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
            max_capacity=5.0,
        )
        new_ctx = ctx.register_capacity(cap)
        assert new_ctx is not ctx

    def test_register_load_returns_new_context(self) -> None:
        """注册负载返回新上下文。/ Register load returns new context."""
        ctx = TaskCompilationContext()
        load = _FakeLoad(resource_key="r1", load_amount=2.0)
        new_ctx = ctx.register_load(load)
        assert new_ctx is not ctx


# ==================== 查询测试 / Query tests =====================


class TestTaskCompilationQuery:
    """查询方法测试。/ Query method tests."""

    def test_get_task_returns_registered(self) -> None:
        """获取已注册任务。/ Get registered task."""
        ctx = TaskCompilationContext()
        task = _FakeTask(task_key="t1", name="Task 1")
        ctx = ctx.register_task(task)
        result = ctx.get_task("t1")
        assert result is not None
        assert result.task_key == "t1"

    def test_get_task_returns_none_for_missing(self) -> None:
        """获取不存在任务返回 None。/ Get missing task returns None."""
        ctx = TaskCompilationContext()
        assert ctx.get_task("nonexistent") is None

    def test_get_all_tasks_returns_registered(self) -> None:
        """获取所有已注册任务。/ Get all registered tasks."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_task(_FakeTask(task_key="t1"))
        ctx = ctx.register_task(_FakeTask(task_key="t2"))
        tasks = ctx.get_all_tasks()
        assert len(tasks) == 2

    def test_get_all_tasks_empty(self) -> None:
        """空上下文获取任务返回空。/ Empty context returns empty tasks."""
        ctx = TaskCompilationContext()
        assert ctx.get_all_tasks() == ()

    def test_assignments_for_task(self) -> None:
        """获取指定任务的分配。/ Get assignments for task."""
        ctx = TaskCompilationContext()
        a1 = _FakeAssignment(task_key="t1", resource_key="r1")
        a2 = _FakeAssignment(task_key="t1", resource_key="r2")
        a3 = _FakeAssignment(task_key="t2", resource_key="r1")
        ctx = ctx.register_assignment(a1)
        ctx = ctx.register_assignment(a2)
        ctx = ctx.register_assignment(a3)
        result = ctx.assignments_for_task("t1")
        assert len(result) == 2

    def test_assignments_for_task_empty(self) -> None:
        """无分配时返回空。/ No assignments returns empty."""
        ctx = TaskCompilationContext()
        assert ctx.assignments_for_task("t1") == ()


# ==================== 容量与负载测试 / Capacity and load tests ===


class TestTaskCompilationCapacityLoad:
    """容量与负载测试。/ Capacity and load tests."""

    def test_total_load_for_resource(self) -> None:
        """计算资源总负载。/ Compute total load for resource."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_load(
            _FakeLoad(resource_key="r1", load_amount=3.0),
        )
        ctx = ctx.register_load(
            _FakeLoad(resource_key="r1", load_amount=2.0),
        )
        ctx = ctx.register_load(
            _FakeLoad(resource_key="r2", load_amount=1.0),
        )
        assert ctx.total_load_for_resource("r1") == 5.0
        assert ctx.total_load_for_resource("r2") == 1.0

    def test_total_load_empty(self) -> None:
        """空负载返回 0。/ Empty load returns 0."""
        ctx = TaskCompilationContext()
        assert ctx.total_load_for_resource("r1") == 0.0

    def test_total_capacity_for_resource(self) -> None:
        """计算资源总容量。/ Compute total capacity for resource."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=5.0,
            ),
        )
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=10.0,
                window_end=20.0,
                max_capacity=3.0,
            ),
        )
        assert ctx.total_capacity_for_resource("r1") == 8.0

    def test_total_capacity_empty(self) -> None:
        """空容量返回 0。/ Empty capacity returns 0."""
        ctx = TaskCompilationContext()
        assert ctx.total_capacity_for_resource("r1") == 0.0

    def test_remaining_capacity_with_exact_match(self) -> None:
        """精确匹配容量记录返回剩余。/ Exact match returns remaining."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=10.0,
            ),
        )
        remaining = ctx.remaining_capacity(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
        )
        assert remaining == 10.0

    def test_remaining_capacity_no_match_no_data(self) -> None:
        """无匹配无数据返回 0。/ No match no data returns 0."""
        ctx = TaskCompilationContext()
        remaining = ctx.remaining_capacity(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
        )
        assert remaining == 0.0


# ==================== 模型构建测试 / Model building tests =========


class TestTaskCompilationModelBuilding:
    """模型构建测试。/ Model building tests."""

    def test_build_model_empty_context(self) -> None:
        """空上下文构建模型成功。/ Empty context build succeeds."""
        ctx = TaskCompilationContext()
        model = ctx.build_model()
        assert model is not None

    def test_build_model_with_assignments(self) -> None:
        """有分配时构建模型成功。/ Build with assignments succeeds."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_assignment(
            _FakeAssignment(task_key="t1", resource_key="r1"),
        )
        model = ctx.build_model()
        assert len(model._variables) > 0

    def test_build_model_with_capacity_constraint(self) -> None:
        """有容量约束时构建模型。/ Build with capacity constraint."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_assignment(
            _FakeAssignment(task_key="t1", resource_key="r1"),
        )
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=5.0,
            ),
        )
        model = ctx.build_model()
        assert len(model._constraints) > 0

    def test_build_model_preserves_name(self) -> None:
        """构建模型保留名称。/ Build model preserves name."""
        ctx = TaskCompilationContext()
        model = ctx.build_model()
        assert model.model_name == "task_compilation"


# ==================== 可行性测试 / Feasibility tests ==============


class TestTaskCompilationFeasibility:
    """可行性测试。/ Feasibility tests."""

    def test_is_feasible_empty_context(self) -> None:
        """空上下文可行。/ Empty context is feasible."""
        ctx = TaskCompilationContext()
        assert ctx.is_feasible() is True

    def test_is_feasible_within_capacity(self) -> None:
        """负载在容量内可行。/ Load within capacity is feasible."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=10.0,
            ),
        )
        ctx = ctx.register_load(
            _FakeLoad(resource_key="r1", load_amount=5.0),
        )
        assert ctx.is_feasible() is True

    def test_is_feasible_exceeds_capacity(self) -> None:
        """负载超过容量不可行。/ Load exceeds capacity infeasible."""
        ctx = TaskCompilationContext()
        ctx = ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=5.0,
            ),
        )
        ctx = ctx.register_load(
            _FakeLoad(resource_key="r1", load_amount=10.0),
        )
        assert ctx.is_feasible() is False


# ==================== 不可变性测试 / Immutability tests ===========


class TestTaskCompilationImmutability:
    """不可变性测试。/ Immutability tests."""

    def test_register_does_not_mutate_original(self) -> None:
        """注册不改变原上下文。/ Register does not mutate original."""
        ctx = TaskCompilationContext()
        ctx.register_task(_FakeTask(task_key="t1"))
        assert len(ctx.get_all_tasks()) == 0

    def test_register_assignment_does_not_mutate(self) -> None:
        """注册分配不改变原上下文。/ Register assignment does not mutate."""
        ctx = TaskCompilationContext()
        ctx.register_assignment(
            _FakeAssignment(task_key="t1", resource_key="r1"),
        )
        assert len(ctx.aggregation.assignments) == 0

    def test_register_capacity_does_not_mutate(self) -> None:
        """注册容量不改变原上下文。/ Register capacity does not mutate."""
        ctx = TaskCompilationContext()
        ctx.register_capacity(
            _FakeCapacity(
                resource_key="r1",
                window_start=0.0,
                window_end=10.0,
                max_capacity=5.0,
            ),
        )
        assert len(ctx.aggregation.capacities) == 0

    def test_register_load_does_not_mutate(self) -> None:
        """注册负载不改变原上下文。/ Register load does not mutate."""
        ctx = TaskCompilationContext()
        ctx.register_load(
            _FakeLoad(resource_key="r1", load_amount=2.0),
        )
        assert len(ctx.aggregation.loads) == 0
