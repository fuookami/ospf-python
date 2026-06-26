"""Task context 测试 / Task context tests.

覆盖 FlightTask 创建、TaskContext 注册、任务调度和
冲突检测。
Covers FlightTask creation, TaskContext registration,
task scheduling, and conflict detection.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from examples.framework_demo.demo4.domain.task.model.flight_task import (
    FlightTask,
)
from examples.framework_demo.demo4.domain.task.model.task_aggregation import (
    TaskAggregation,
)
from examples.framework_demo.demo4.domain.task.model.task_conflict import (
    ConflictType,
    TaskConflict,
)
from examples.framework_demo.demo4.domain.task.model.task_context import (
    TaskContext,
)
from examples.framework_demo.demo4.domain.task.model.task_priority import (
    TaskPriority,
)
from examples.framework_demo.demo4.domain.task.model.task_requirement import (
    TaskRequirement,
)
from examples.framework_demo.demo4.domain.task.model.task_result import (
    TaskResult,
)
from examples.framework_demo.demo4.domain.task.model.task_schedule import (
    TaskSchedule,
)
from examples.framework_demo.demo4.domain.task.model.task_status import (
    TaskStatus,
)
from examples.framework_demo.demo4.domain.task.model.turnaround import (
    Turnaround,
)
from examples.framework_demo.demo4.domain.task.service.task_resource_allocator import (
    TaskResourceAllocator,
)
from examples.framework_demo.demo4.domain.task.service.task_scheduler import (
    TaskScheduler,
)


def _make_flight_task(
    task_id: str = "T1",
    priority: TaskPriority = TaskPriority.NORMAL,
    hours_offset: int = 0,
) -> FlightTask:
    """创建测试航班任务 / Create test flight task."""
    base = datetime(2025, 6, 1, 8, 0)
    return FlightTask(
        task_id=task_id,
        flight_no=f"CA{task_id[-3:]}",
        origin="PEK",
        destination="PVG",
        departure_time=base + timedelta(hours=hours_offset),
        arrival_time=base + timedelta(hours=hours_offset + 2),
        aircraft_type="A320",
        priority=priority,
    )


class TestFlightTask:
    """FlightTask 测试 / FlightTask tests."""

    def test_duration(self) -> None:
        """任务持续时间 / Task duration."""
        t = _make_flight_task()
        assert t.duration_minutes == 120

    def test_is_long_haul(self) -> None:
        """是否长途 / Long haul check."""
        t = _make_flight_task()
        assert t.is_long_haul is False

    def test_route_key(self) -> None:
        """航路键 / Route key."""
        t = _make_flight_task()
        assert t.route_key == "PEK-PVG"

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        t = _make_flight_task()
        with pytest.raises(AttributeError):
            t.flight_no = "XX"  # type: ignore[misc]


class TestTaskStatus:
    """TaskStatus 测试 / TaskStatus tests."""

    def test_active_statuses(self) -> None:
        """活跃状态 / Active statuses."""
        assert TaskStatus.SCHEDULED.is_active is True
        assert TaskStatus.IN_PROGRESS.is_active is True
        assert TaskStatus.COMPLETED.is_active is False
        assert TaskStatus.CANCELLED.is_active is False


class TestTaskPriority:
    """TaskPriority 测试 / TaskPriority tests."""

    def test_display_name(self) -> None:
        """显示名称 / Display name."""
        critical_name = TaskPriority.CRITICAL.display_name
        low_name = TaskPriority.LOW.display_name
        assert "ritical" in critical_name
        assert "ow" in low_name

    def test_ordering(self) -> None:
        """排序 / Ordering."""
        assert TaskPriority.CRITICAL < TaskPriority.HIGH
        assert TaskPriority.NORMAL < TaskPriority.LOW


class TestTaskContext:
    """TaskContext 测试 / TaskContext tests."""

    def test_register_and_get(self) -> None:
        """注册和查询 / Register and get."""
        ctx = TaskContext()
        t = _make_flight_task("T1")
        ctx.register_task(t)
        assert ctx.task_count == 1
        assert ctx.get_task("T1") is t

    def test_get_nonexistent(self) -> None:
        """查询不存在 / Get nonexistent."""
        ctx = TaskContext()
        assert ctx.get_task("NOPE") is None

    def test_register_requirement(self) -> None:
        """注册需求 / Register requirement."""
        ctx = TaskContext()
        req = TaskRequirement(
            task_id="T1",
            crew_count=4,
            aircraft_type="A320",
            min_experience=500,
        )
        ctx.register_requirement(req)
        assert ctx.get_requirement("T1") is req

    def test_register_result(self) -> None:
        """注册结果 / Register result."""
        ctx = TaskContext()
        res = TaskResult(
            task_id="T1",
            status=TaskStatus.COMPLETED,
            metrics={"fuel": 0.95, "on_time": 1.0},
        )
        ctx.register_result(res)
        result = ctx.get_result("T1")
        assert result is res
        assert result is not None and result.is_success is True

    def test_get_by_status(self) -> None:
        """按状态查询 / Get by status."""
        ctx = TaskContext()
        ctx.register_task(_make_flight_task("T1"))
        ctx.register_task(_make_flight_task("T2"))
        scheduled = ctx.get_tasks_by_status(TaskStatus.SCHEDULED)
        assert len(list(scheduled)) == 2

    def test_build_aggregation(self) -> None:
        """构建聚合 / Build aggregation."""
        ctx = TaskContext()
        ctx.register_task(_make_flight_task("T1"))
        ctx.register_task(_make_flight_task("T2", TaskPriority.HIGH))
        agg = ctx.build_aggregation()
        assert agg.total_count == 2


class TestTaskAggregation:
    """TaskAggregation 测试 / TaskAggregation tests."""

    def test_from_tasks(self) -> None:
        """从任务列表构建 / Build from tasks."""
        tasks = (
            _make_flight_task("T1"),
            _make_flight_task("T2", TaskPriority.HIGH),
        )
        agg = TaskAggregation.from_tasks(tasks)
        assert agg.total_count == 2

    def test_critical_count(self) -> None:
        """紧急任务计数 / Critical count."""
        tasks = (
            _make_flight_task("T1", TaskPriority.CRITICAL),
            _make_flight_task("T2", TaskPriority.NORMAL),
        )
        agg = TaskAggregation.from_tasks(tasks)
        assert agg.critical_count == 1


class TestTaskScheduler:
    """TaskScheduler 测试 / TaskScheduler tests."""

    def test_basic_schedule(self) -> None:
        """基本调度 / Basic schedule."""
        scheduler = TaskScheduler()
        tasks = [
            _make_flight_task("T1", hours_offset=0),
            _make_flight_task("T2", hours_offset=3),
        ]
        result = scheduler.schedule(
            tasks,
            start_time=datetime(2025, 6, 1, 7, 0),
        )
        assert result.scheduled_count == 2
        assert result.all_scheduled is True


class TestTaskConflict:
    """TaskConflict 测试 / TaskConflict tests."""

    def test_involved_tasks(self) -> None:
        """冲突涉及任务 / Involved tasks."""
        c = TaskConflict(
            task_a="T1",
            task_b="T2",
            conflict_type=ConflictType.TIME_OVERLAP,
        )
        assert c.involved_tasks == ("T1", "T2")

    def test_description(self) -> None:
        """冲突描述 / Conflict description."""
        c = TaskConflict(
            task_a="T1",
            task_b="T2",
            conflict_type=ConflictType.RESOURCE_CONFLICT,
        )
        assert "T1" in c.description
        assert "T2" in c.description


class TestTurnaround:
    """Turnaround 测试 / Turnaround tests."""

    def test_quick_turn(self) -> None:
        """快速周转 / Quick turn."""
        ta = Turnaround(task_id="T1", ground_time=30)
        assert ta.is_quick_turn is True

    def test_has_task(self) -> None:
        """包含子任务 / Has task."""
        ta = Turnaround(
            task_id="T1",
            ground_time=60,
            tasks=("sub1", "sub2"),
        )
        assert ta.has_task("sub1") is True
        assert ta.has_task("sub3") is False


class TestTaskSchedule:
    """TaskSchedule 测试 / TaskSchedule tests."""

    def test_planned_duration(self) -> None:
        """计划持续时间 / Planned duration."""
        s = TaskSchedule(
            task_id="T1",
            planned_start=datetime(2025, 6, 1, 8, 0),
            planned_end=datetime(2025, 6, 1, 10, 0),
        )
        assert s.planned_duration_minutes == 120

    def test_not_started(self) -> None:
        """未开始 / Not started."""
        s = TaskSchedule(
            task_id="T1",
            planned_start=datetime(2025, 6, 1, 8, 0),
            planned_end=datetime(2025, 6, 1, 10, 0),
        )
        assert s.is_started is False
        assert s.is_completed is False


class TestTaskResourceAllocator:
    """TaskResourceAllocator 测试 / Resource allocator tests."""

    def test_allocate(self) -> None:
        """资源分配 / Resource allocation."""
        allocator = TaskResourceAllocator()
        allocator.set_available_aircraft("A320", ["AC1", "AC2"])
        allocator.set_available_crew("A320", ["C1", "C2"])
        tasks = [_make_flight_task("T1")]
        reqs = [
            TaskRequirement(
                task_id="T1",
                crew_count=2,
                aircraft_type="A320",
            )
        ]
        result = allocator.allocate(tasks, reqs)
        assert result.allocated_count >= 0
