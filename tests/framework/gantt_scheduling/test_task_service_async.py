"""任务异步服务测试。

Task async service tests.

测试 TaskServiceAsync 抽象基类及其具体子类的
调度、验证、关键路径和批量验证功能。
Tests TaskServiceAsync ABC and concrete subclass for
scheduling, validation, critical path, and batch validation.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
    Task,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_service_async import (
    TaskServiceAsync,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

# ── concrete implementation ────────────────────────────────────


class _StubTaskService(TaskServiceAsync):
    """桩实现用于测试。/ Stub implementation for testing."""

    async def schedule_tasks(
        self,
        context: TaskContext,
    ) -> Result:
        """返回空聚合结果。/ Return empty aggregation."""
        return Ok(None)

    async def validate_task(
        self,
        task: Task,
    ) -> Result:
        """始终验证通过。/ Always validates."""
        return Ok(None)

    async def compute_critical_path(
        self,
        tasks: tuple[Task, ...],
    ) -> Result:
        """返回任务键列表。/ Return task key list."""
        keys = tuple(t.task_key for t in tasks)
        return Ok(keys)

    async def estimate_duration(
        self,
        tasks: tuple[Task, ...],
    ) -> Result:
        """返回总持续时间。/ Return total duration."""
        total = sum(t.duration for t in tasks)
        return Ok(total)


class _FailingValidationService(TaskServiceAsync):
    """验证失败的服务。/ Service with failing validation."""

    async def schedule_tasks(
        self,
        context: TaskContext,
    ) -> Result:
        return Ok(None)

    async def validate_task(
        self,
        task: Task,
    ) -> Result:
        """始终验证失败。/ Always validation fails."""
        return Failed(
            Err(
                _code="INVALID",
                _message=f"invalid: {task.task_key}",
            )
        )

    async def compute_critical_path(
        self,
        tasks: tuple[Task, ...],
    ) -> Result:
        return Ok(())

    async def estimate_duration(
        self,
        tasks: tuple[Task, ...],
    ) -> Result:
        return Ok(0.0)


# ── helpers ────────────────────────────────────────────────────


def _make_task(
    key: str = "t1",
    duration: float = 10.0,
    priority: int = 0,
) -> Task:
    """创建测试任务。/ Create test task."""
    return Task(
        task_key=key,
        name=f"Task {key}",
        duration=duration,
        priority=priority,
    )


# ── ABC tests ──────────────────────────────────────────────────


class TestTaskServiceAsyncABC:
    """抽象基类测试。/ ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化。/ Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            TaskServiceAsync()  # type: ignore[abstract]

    def test_subclass_can_instantiate(self) -> None:
        """子类可以实例化。/ Subclass can instantiate."""
        svc = _StubTaskService()
        assert svc is not None


# ── schedule_tasks tests ───────────────────────────────────────


class TestScheduleTasks:
    """调度任务测试。/ Schedule tasks tests."""

    @pytest.mark.asyncio
    async def test_schedule_tasks_returns_ok(self) -> None:
        """调度返回成功。/ Schedule returns ok."""
        svc = _StubTaskService()
        ctx = TaskContext()
        result = await svc.schedule_tasks(ctx)
        assert result.is_ok() is True

    @pytest.mark.asyncio
    async def test_schedule_tasks_with_registered(self) -> None:
        """带注册任务的调度。/ Schedule with registered tasks."""
        svc = _StubTaskService()
        ctx = TaskContext()
        task = _make_task("t1")
        ctx.register(task)
        result = await svc.schedule_tasks(ctx)
        assert result.is_ok() is True


# ── validate_task tests ────────────────────────────────────────


class TestValidateTask:
    """验证任务测试。/ Validate task tests."""

    @pytest.mark.asyncio
    async def test_validate_passes(self) -> None:
        """验证通过。/ Validation passes."""
        svc = _StubTaskService()
        task = _make_task()
        result = await svc.validate_task(task)
        assert result.is_ok() is True

    @pytest.mark.asyncio
    async def test_validate_fails(self) -> None:
        """验证失败。/ Validation fails."""
        svc = _FailingValidationService()
        task = _make_task()
        result = await svc.validate_task(task)
        assert result.is_failed() is True


# ── compute_critical_path tests ────────────────────────────────


class TestComputeCriticalPath:
    """关键路径测试。/ Critical path tests."""

    @pytest.mark.asyncio
    async def test_critical_path_empty(self) -> None:
        """空任务返回空路径。/ Empty tasks return empty path."""
        svc = _StubTaskService()
        result = await svc.compute_critical_path(())
        assert result.is_ok() is True
        assert result.unwrap() == ()

    @pytest.mark.asyncio
    async def test_critical_path_single(self) -> None:
        """单任务路径。/ Single task path."""
        svc = _StubTaskService()
        tasks = (_make_task("t1"),)
        result = await svc.compute_critical_path(tasks)
        assert result.unwrap() == ("t1",)

    @pytest.mark.asyncio
    async def test_critical_path_multiple(self) -> None:
        """多任务路径。/ Multiple task path."""
        svc = _StubTaskService()
        tasks = (
            _make_task("t1"),
            _make_task("t2"),
            _make_task("t3"),
        )
        result = await svc.compute_critical_path(tasks)
        assert result.unwrap() == ("t1", "t2", "t3")


# ── estimate_duration tests ────────────────────────────────────


class TestEstimateDuration:
    """估算时长测试。/ Estimate duration tests."""

    @pytest.mark.asyncio
    async def test_estimate_empty(self) -> None:
        """空任务时长为 0。/ Empty tasks duration is 0."""
        svc = _StubTaskService()
        result = await svc.estimate_duration(())
        assert result.unwrap() == 0.0

    @pytest.mark.asyncio
    async def test_estimate_single(self) -> None:
        """单任务时长。/ Single task duration."""
        svc = _StubTaskService()
        tasks = (_make_task("t1", duration=30.0),)
        result = await svc.estimate_duration(tasks)
        assert result.unwrap() == 30.0

    @pytest.mark.asyncio
    async def test_estimate_multiple(self) -> None:
        """多任务总时长。/ Multiple tasks total duration."""
        svc = _StubTaskService()
        tasks = (
            _make_task("t1", duration=10.0),
            _make_task("t2", duration=20.0),
        )
        result = await svc.estimate_duration(tasks)
        assert result.unwrap() == 30.0


# ── schedule_single_task tests ─────────────────────────────────


class TestScheduleSingleTask:
    """单任务调度测试。/ Single task schedule tests."""

    @pytest.mark.asyncio
    async def test_schedule_existing_task(self) -> None:
        """调度已注册任务。/ Schedule registered task."""
        svc = _StubTaskService()
        ctx = TaskContext()
        task = _make_task("t1")
        ctx.register(task)
        result = await svc.schedule_single_task(ctx, "t1")
        assert result.is_ok() is True

    @pytest.mark.asyncio
    async def test_schedule_missing_task_fails(self) -> None:
        """调度未注册任务失败。

        Schedule unregistered task fails.
        """
        svc = _StubTaskService()
        ctx = TaskContext()
        result = await svc.schedule_single_task(ctx, "missing")
        assert result.is_failed() is True


# ── batch_validate tests ───────────────────────────────────────


class TestBatchValidate:
    """批量验证测试。/ Batch validate tests."""

    @pytest.mark.asyncio
    async def test_batch_validate_empty(self) -> None:
        """空任务验证通过。/ Empty batch validates."""
        svc = _StubTaskService()
        result = await svc.batch_validate(())
        assert result.is_ok() is True

    @pytest.mark.asyncio
    async def test_batch_validate_all_pass(self) -> None:
        """全部通过。/ All pass."""
        svc = _StubTaskService()
        tasks = (
            _make_task("t1"),
            _make_task("t2"),
        )
        result = await svc.batch_validate(tasks)
        assert result.is_ok() is True

    @pytest.mark.asyncio
    async def test_batch_validate_first_fails(self) -> None:
        """首个失败时返回失败。/ First failure returns failed."""
        svc = _FailingValidationService()
        tasks = (
            _make_task("t1"),
            _make_task("t2"),
        )
        result = await svc.batch_validate(tasks)
        assert result.is_failed() is True
