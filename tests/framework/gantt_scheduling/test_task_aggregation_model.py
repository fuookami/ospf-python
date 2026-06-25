"""TaskAggregation model tests / 任务聚合模型测试.

Exercises TaskAggregation factory methods, queries, and mutation.
覆盖 TaskAggregation 的工厂方法、查询和变更操作。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_aggregation import (
    TaskAggregation,
)


def _make_task(
    key: str,
    duration: float = 5.0,
    priority: int = 0,
    earliest_start: float = 0.0,
    deadline: float = float("inf"),
    slack: float = 0.0,
) -> Task:
    """Helper to create a Task. / 创建 Task 的辅助函数."""
    return Task(
        task_key=key,
        name=f"Task-{key}",
        duration=duration,
        priority=priority,
        earliest_start=earliest_start,
        deadline=deadline,
    )


class TestTaskAggregationFactory:
    """Factory method tests / 工厂方法测试."""

    def test_create_empty(self) -> None:
        """Create from empty task list. / 从空任务列表创建."""
        agg = TaskAggregation.create(tasks=())
        assert agg.size == 0
        assert agg.is_empty is True
        assert agg.total_duration == pytest.approx(0.0)
        assert agg.critical_path == ()

    def test_create_with_tasks(self) -> None:
        """Create with tasks computes duration. / 创建时计算时长."""
        t1 = _make_task("t1", duration=5.0, earliest_start=0.0)
        t2 = _make_task("t2", duration=3.0, earliest_start=5.0)
        agg = TaskAggregation.create(tasks=(t1, t2))
        assert agg.size == 2
        assert agg.is_empty is False
        assert agg.total_duration == pytest.approx(8.0)

    def test_empty_factory(self) -> None:
        """Empty factory method. / 空工厂方法."""
        agg = TaskAggregation.empty()
        assert agg.size == 0
        assert agg.total_duration == pytest.approx(0.0)
        assert agg.critical_path == ()

    def test_frozen(self) -> None:
        """Immutable dataclass. / 不可变数据类."""
        agg = TaskAggregation.empty()
        with pytest.raises(AttributeError):
            agg.total_duration = 1.0  # type: ignore[misc]


class TestTaskAggregationProperties:
    """Property tests / 属性测试."""

    def test_task_keys(self) -> None:
        """Task keys tuple. / 任务键元组."""
        t1 = _make_task("a")
        t2 = _make_task("b")
        agg = TaskAggregation.create(tasks=(t1, t2))
        assert agg.task_keys == ("a", "b")

    def test_critical_path_with_slack_zero(self) -> None:
        """Critical path picks zero-slack tasks. / 关键路径选取零松弛任务."""
        t1 = _make_task("t1", duration=5.0, deadline=5.0)
        t2 = _make_task("t2", duration=3.0, deadline=100.0)
        agg = TaskAggregation.create(tasks=(t1, t2))
        assert "t1" in agg.critical_path

    def test_critical_path_empty(self) -> None:
        """Critical path empty for no tasks. / 无任务时关键路径为空."""
        agg = TaskAggregation.empty()
        assert agg.critical_path_length == 0

    def test_critical_path_fallback_longest(self) -> None:
        """Fallback: longest task when no zero-slack. / 无零松弛时取最长任务."""
        t1 = _make_task("t1", duration=10.0, deadline=100.0)
        t2 = _make_task("t2", duration=3.0, deadline=100.0)
        agg = TaskAggregation.create(tasks=(t1, t2))
        assert "t1" in agg.critical_path


class TestTaskAggregationMutation:
    """Mutation tests (immutable returns) / 变更测试（不可变返回）."""

    def test_add_tasks(self) -> None:
        """Add new tasks returns new aggregation. / 添加任务返回新聚合."""
        t1 = _make_task("t1")
        agg = TaskAggregation.create(tasks=(t1,))
        t2 = _make_task("t2")
        new_agg = agg.add_tasks((t2,))
        assert new_agg.size == 2
        assert agg.size == 1

    def test_add_tasks_deduplicates(self) -> None:
        """Add tasks deduplicates by key. / 添加任务按键去重."""
        t1 = _make_task("t1", duration=5.0)
        t1_dup = _make_task("t1", duration=10.0)
        agg = TaskAggregation.create(tasks=(t1,))
        new_agg = agg.add_tasks((t1_dup,))
        assert new_agg.size == 1
        assert new_agg.tasks[0].duration == pytest.approx(5.0)

    def test_remove_task(self) -> None:
        """Remove task by key. / 按键移除任务."""
        t1 = _make_task("t1")
        t2 = _make_task("t2")
        agg = TaskAggregation.create(tasks=(t1, t2))
        new_agg = agg.remove_task("t1")
        assert new_agg.size == 1
        assert new_agg.task_keys == ("t2",)

    def test_get_task_found(self) -> None:
        """Get existing task. / 获取已有任务."""
        t1 = _make_task("t1")
        agg = TaskAggregation.create(tasks=(t1,))
        assert agg.get_task("t1") is t1

    def test_get_task_not_found(self) -> None:
        """Get missing task returns None. / 获取缺失任务返回 None."""
        agg = TaskAggregation.empty()
        assert agg.get_task("missing") is None

    def test_contains_true(self) -> None:
        """Contains existing task. / 包含已有任务."""
        t1 = _make_task("t1")
        agg = TaskAggregation.create(tasks=(t1,))
        assert agg.contains("t1") is True

    def test_contains_false(self) -> None:
        """Does not contain missing task. / 不包含缺失任务."""
        agg = TaskAggregation.empty()
        assert agg.contains("missing") is False

    def test_with_critical_path(self) -> None:
        """Create with different critical path. / 创建不同关键路径的聚合."""
        t1 = _make_task("t1", duration=5.0, deadline=5.0)
        agg = TaskAggregation.create(tasks=(t1,))
        assert "t1" in agg.critical_path
        new_agg = agg.with_critical_path(("t3",))
        assert new_agg.critical_path == ("t3",)
        assert agg.critical_path == ("t1",)
