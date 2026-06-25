"""TaskContext model tests / 任务上下文模型测试.

Exercises TaskContext registration, queries, and filtering.
覆盖 TaskContext 的注册、查询和过滤操作。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)


def _make_task(
    key: str,
    priority: int = 0,
    resources: tuple[tuple[str, float], ...] = (),
) -> Task:
    """Helper to create a Task. / 创建 Task 的辅助函数."""
    return Task(
        task_key=key,
        name=f"Task-{key}",
        duration=5.0,
        priority=priority,
        resource_requirements=resources,
    )


class TestTaskContextRegister:
    """Registration tests / 注册测试."""

    def test_register_ok(self) -> None:
        """Register returns Ok. / 注册返回 Ok."""
        ctx = TaskContext()
        result = ctx.register(_make_task("t1"))
        assert result.is_ok()
        assert ctx.size == 1

    def test_register_duplicate(self) -> None:
        """Duplicate key returns Failed. / 重复键返回 Failed."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        result = ctx.register(_make_task("t1"))
        assert result.is_failed()

    def test_unregister_ok(self) -> None:
        """Unregister existing task. / 注销已有任务."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        result = ctx.unregister("t1")
        assert result.is_ok()
        assert ctx.size == 0

    def test_unregister_missing(self) -> None:
        """Unregister missing task returns Failed. / 注销缺失任务返回 Failed."""
        ctx = TaskContext()
        result = ctx.unregister("missing")
        assert result.is_failed()

    def test_clear(self) -> None:
        """Clear all tasks. / 清空所有任务."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        ctx.register(_make_task("t2"))
        ctx.clear()
        assert ctx.is_empty is True


class TestTaskContextQueries:
    """Query tests / 查询测试."""

    def test_get_existing(self) -> None:
        """Get existing task. / 获取已有任务."""
        ctx = TaskContext()
        t = _make_task("t1")
        ctx.register(t)
        assert ctx.get("t1") is t

    def test_get_missing(self) -> None:
        """Get missing task returns None. / 获取缺失任务返回 None."""
        ctx = TaskContext()
        assert ctx.get("missing") is None

    def test_get_or_error_ok(self) -> None:
        """Get or error returns Ok. / 获取或错误返回 Ok."""
        ctx = TaskContext()
        t = _make_task("t1")
        ctx.register(t)
        result = ctx.get_or_error("t1")
        assert result.is_ok()

    def test_get_or_error_failed(self) -> None:
        """Get or error returns Failed. / 获取或错误返回 Failed."""
        ctx = TaskContext()
        result = ctx.get_or_error("missing")
        assert result.is_failed()

    def test_tasks_tuple(self) -> None:
        """All tasks as tuple. / 所有任务元组."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        ctx.register(_make_task("t2"))
        assert len(ctx.tasks()) == 2

    def test_task_keys(self) -> None:
        """All task keys. / 所有任务键."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        ctx.register(_make_task("t2"))
        keys = ctx.task_keys()
        assert "t1" in keys
        assert "t2" in keys

    def test_contains_true(self) -> None:
        """Contains existing key. / 包含已有键."""
        ctx = TaskContext()
        ctx.register(_make_task("t1"))
        assert ctx.contains("t1") is True

    def test_contains_false(self) -> None:
        """Does not contain missing key. / 不包含缺失键."""
        ctx = TaskContext()
        assert ctx.contains("missing") is False

    def test_size_and_is_empty(self) -> None:
        """Size and empty check. / 大小和空检查."""
        ctx = TaskContext()
        assert ctx.size == 0
        assert ctx.is_empty is True
        ctx.register(_make_task("t1"))
        assert ctx.size == 1
        assert ctx.is_empty is False


class TestTaskContextFilter:
    """Filter tests / 过滤测试."""

    def test_filter_by_priority(self) -> None:
        """Filter by minimum priority. / 按最低优先级过滤."""
        ctx = TaskContext()
        ctx.register(_make_task("t1", priority=1))
        ctx.register(_make_task("t2", priority=5))
        ctx.register(_make_task("t3", priority=3))
        result = ctx.filter_by_priority(3)
        keys = {t.task_key for t in result}
        assert keys == {"t2", "t3"}

    def test_filter_by_resource(self) -> None:
        """Filter by resource requirement. / 按资源需求过滤."""
        ctx = TaskContext()
        ctx.register(_make_task("t1", resources=(("r1", 2.0),)))
        ctx.register(_make_task("t2", resources=(("r2", 1.0),)))
        result = ctx.filter_by_resource("r1")
        assert len(result) == 1
        assert result[0].task_key == "t1"
