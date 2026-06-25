"""Task model tests / 任务模型测试.

Exercises Task creation, properties, and methods.
覆盖 Task 的创建、属性和方法。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import TaskType


class TestTaskCreate:
    """Task creation tests / 任务创建测试."""

    def test_create_factory(self) -> None:
        """Factory method creates valid instance. / 工厂方法创建有效实例."""
        t = Task.create(
            task_key="t1",
            name="Cut",
            duration=5.0,
            priority=2,
            earliest_start=1.0,
            deadline=20.0,
            resource_requirements=(("r1", 3.0),),
            task_type=TaskType.VARIABLE,
        )
        assert t.task_key == "t1"
        assert t.name == "Cut"
        assert t.duration == pytest.approx(5.0)
        assert t.priority == 2
        assert t.earliest_start == pytest.approx(1.0)
        assert t.deadline == pytest.approx(20.0)
        assert t.resource_requirements == (("r1", 3.0),)
        assert t.task_type is TaskType.VARIABLE

    def test_create_defaults(self) -> None:
        """Default parameters. / 默认参数."""
        t = Task(task_key="t1", name="X", duration=1.0)
        assert t.priority == 0
        assert t.earliest_start == pytest.approx(0.0)
        assert t.deadline == float("inf")
        assert t.resource_requirements == ()
        assert t.task_type is TaskType.FIXED

    def test_frozen(self) -> None:
        """Immutable dataclass. / 不可变数据类."""
        t = Task(task_key="t1", name="X", duration=1.0)
        with pytest.raises(AttributeError):
            t.duration = 2.0  # type: ignore[misc]


class TestTaskProperties:
    """Task property tests / 任务属性测试."""

    def test_latest_start_with_deadline(self) -> None:
        """Latest start = deadline - duration. / 最晚开始 = 截止 - 时长."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            deadline=20.0,
        )
        assert t.latest_start == pytest.approx(15.0)

    def test_latest_start_infinite_deadline(self) -> None:
        """Infinite deadline yields inf. / 无穷截止时间返回 inf."""
        t = Task(task_key="t1", name="X", duration=5.0)
        assert t.latest_start == float("inf")

    def test_latest_start_clamped_to_zero(self) -> None:
        """Latest start clamped to 0. / 最晚开始截断为 0."""
        t = Task(
            task_key="t1",
            name="X",
            duration=10.0,
            deadline=5.0,
        )
        assert t.latest_start == pytest.approx(0.0)

    def test_earliest_end(self) -> None:
        """Earliest end = earliest_start + duration. / 最早结束."""
        t = Task(
            task_key="t1",
            name="X",
            duration=3.0,
            earliest_start=2.0,
        )
        assert t.earliest_end == pytest.approx(5.0)

    def test_time_window_finite(self) -> None:
        """Finite time window. / 有限时间窗口."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            earliest_start=2.0,
            deadline=20.0,
        )
        assert t.time_window == pytest.approx(18.0)

    def test_time_window_infinite(self) -> None:
        """Infinite time window. / 无穷时间窗口."""
        t = Task(task_key="t1", name="X", duration=5.0)
        assert t.time_window == float("inf")

    def test_slack(self) -> None:
        """Slack = latest_start - earliest_start. / 松弛时间."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            earliest_start=2.0,
            deadline=20.0,
        )
        assert t.slack == pytest.approx(13.0)

    def test_slack_no_slack(self) -> None:
        """Zero slack when deadline is tight. / 截止紧张时松弛为 0."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            earliest_start=0.0,
            deadline=5.0,
        )
        assert t.slack == pytest.approx(0.0)

    def test_resource_keys(self) -> None:
        """Deduplicated resource keys. / 去重资源键."""
        t = Task(
            task_key="t1",
            name="X",
            duration=1.0,
            resource_requirements=(("r1", 2.0), ("r2", 1.0), ("r1", 3.0)),
        )
        assert t.resource_keys == ("r1", "r2")

    def test_resource_keys_empty(self) -> None:
        """Empty resource keys. / 空资源键."""
        t = Task(task_key="t1", name="X", duration=1.0)
        assert t.resource_keys == ()


class TestTaskMethods:
    """Task method tests / 任务方法测试."""

    def test_resource_demand(self) -> None:
        """Sum demand for specific resource. / 指定资源总需求."""
        t = Task(
            task_key="t1",
            name="X",
            duration=1.0,
            resource_requirements=(("r1", 2.0), ("r2", 1.0), ("r1", 3.0)),
        )
        assert t.resource_demand("r1") == pytest.approx(5.0)
        assert t.resource_demand("r2") == pytest.approx(1.0)

    def test_resource_demand_missing(self) -> None:
        """Zero demand for missing resource. / 缺失资源零需求."""
        t = Task(task_key="t1", name="X", duration=1.0)
        assert t.resource_demand("unknown") == pytest.approx(0.0)

    def test_requires_resource_true(self) -> None:
        """Requires existing resource. / 需要已有资源."""
        t = Task(
            task_key="t1",
            name="X",
            duration=1.0,
            resource_requirements=(("r1", 2.0),),
        )
        assert t.requires_resource("r1") is True

    def test_requires_resource_false(self) -> None:
        """Does not require missing resource. / 不需要缺失资源."""
        t = Task(task_key="t1", name="X", duration=1.0)
        assert t.requires_resource("r1") is False

    def test_is_feasible_in_window(self) -> None:
        """Feasible in sufficient window. / 足够窗口可行."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            earliest_start=0.0,
            deadline=20.0,
        )
        assert t.is_feasible_in_window(0.0, 20.0) is True

    def test_is_feasible_in_window_too_small(self) -> None:
        """Infeasible in tight window. / 窗口过小不可行."""
        t = Task(
            task_key="t1",
            name="X",
            duration=10.0,
            earliest_start=0.0,
            deadline=20.0,
        )
        assert t.is_feasible_in_window(0.0, 5.0) is False

    def test_with_deadline(self) -> None:
        """Create copy with new deadline. / 创建不同截止时间的副本."""
        t = Task(
            task_key="t1",
            name="X",
            duration=5.0,
            deadline=20.0,
        )
        t2 = t.with_deadline(30.0)
        assert t2.deadline == pytest.approx(30.0)
        assert t2.task_key == "t1"
        assert t.deadline == pytest.approx(20.0)

    def test_str(self) -> None:
        """String representation. / 字符串表示."""
        t = Task(task_key="t1", name="Cut", duration=1.0)
        assert str(t) == "Task(t1: Cut)"
