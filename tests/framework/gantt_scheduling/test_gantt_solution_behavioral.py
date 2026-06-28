"""GanttSolution behavioral tests.

Covers GanttSolution properties and query methods with realistic data.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)


def _make_utilization(
    resource_key: str = "r1",
    total: float = 10.0,
    used: float = 5.0,
) -> ResourceUtilization:
    return ResourceUtilization(
        resource_key=resource_key,
        time_range_start=0.0,
        time_range_end=10.0,
        total_capacity=total,
        used_capacity=used,
        peak_usage=used,
    )


# ==================== TaskScheduleEntry tests ====================


class TestTaskScheduleEntry:
    """TaskScheduleEntry behavioral tests."""

    def test_default_assigned_resource_is_empty(self) -> None:
        entry = TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=5.0)
        assert entry.assigned_resource == ""

    def test_custom_assigned_resource(self) -> None:
        entry = TaskScheduleEntry(
            task_key="t1", start_time=0.0, end_time=5.0, assigned_resource="r1"
        )
        assert entry.assigned_resource == "r1"

    def test_frozen(self) -> None:
        entry = TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=5.0)
        with pytest.raises(AttributeError):
            entry.task_key = "t2"  # type: ignore[misc]


# ==================== GanttSolution construction tests ====================


class TestGanttSolutionConstruction:
    """GanttSolution construction and defaults."""

    def test_default_name(self) -> None:
        sol = GanttSolution()
        assert sol.name == "gantt solution"

    def test_default_schedule_empty(self) -> None:
        sol = GanttSolution()
        assert sol.schedule == ()

    def test_default_makespan_zero(self) -> None:
        sol = GanttSolution()
        assert sol.makespan == pytest.approx(0.0)

    def test_default_not_optimal(self) -> None:
        sol = GanttSolution()
        assert sol.is_optimal is False

    def test_with_schedule(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
            TaskScheduleEntry(task_key="t2", start_time=3.0, end_time=5.0, assigned_resource="r1"),
        )
        sol = GanttSolution(name="test", schedule=entries, makespan=5.0)
        assert sol.task_count == 2
        assert sol.makespan == pytest.approx(5.0)

    def test_frozen(self) -> None:
        sol = GanttSolution()
        with pytest.raises(AttributeError):
            sol.name = "x"  # type: ignore[misc]


# ==================== GanttSolution query tests ====================


class TestGanttSolutionTaskCount:
    """task_count and has_schedule tests."""

    def test_task_count_empty(self) -> None:
        sol = GanttSolution()
        assert sol.task_count == 0

    def test_task_count_with_entries(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0),
            TaskScheduleEntry(task_key="t2", start_time=0.0, end_time=2.0),
            TaskScheduleEntry(task_key="t3", start_time=0.0, end_time=4.0),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.task_count == 3

    def test_has_schedule_false_when_empty(self) -> None:
        sol = GanttSolution()
        assert sol.has_schedule is False

    def test_has_schedule_true_with_entries(self) -> None:
        entries = (TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0),)
        sol = GanttSolution(schedule=entries)
        assert sol.has_schedule is True


class TestGanttSolutionResourceCount:
    """resource_count tests."""

    def test_resource_count_no_resources(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.resource_count == 0

    def test_resource_count_single(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.resource_count == 1

    def test_resource_count_deduplication(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
            TaskScheduleEntry(task_key="t2", start_time=0.0, end_time=2.0, assigned_resource="r1"),
            TaskScheduleEntry(task_key="t3", start_time=0.0, end_time=4.0, assigned_resource="r2"),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.resource_count == 2


class TestGanttSolutionEntryFor:
    """entry_for tests."""

    def test_entry_for_found(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
            TaskScheduleEntry(task_key="t2", start_time=3.0, end_time=5.0, assigned_resource="r2"),
        )
        sol = GanttSolution(schedule=entries)
        entry = sol.entry_for("t1")
        assert entry is not None
        assert entry.task_key == "t1"
        assert entry.start_time == pytest.approx(0.0)

    def test_entry_for_not_found(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.entry_for("t99") is None

    def test_entry_for_empty_schedule(self) -> None:
        sol = GanttSolution()
        assert sol.entry_for("t1") is None


class TestGanttSolutionEntriesForResource:
    """entries_for_resource tests."""

    def test_entries_for_resource_found(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
            TaskScheduleEntry(task_key="t2", start_time=3.0, end_time=5.0, assigned_resource="r2"),
            TaskScheduleEntry(task_key="t3", start_time=5.0, end_time=8.0, assigned_resource="r1"),
        )
        sol = GanttSolution(schedule=entries)
        r1_entries = sol.entries_for_resource("r1")
        assert len(r1_entries) == 2
        assert r1_entries[0].task_key == "t1"
        assert r1_entries[1].task_key == "t3"

    def test_entries_for_resource_not_found(self) -> None:
        entries = (
            TaskScheduleEntry(task_key="t1", start_time=0.0, end_time=3.0, assigned_resource="r1"),
        )
        sol = GanttSolution(schedule=entries)
        assert sol.entries_for_resource("r99") == ()

    def test_entries_for_resource_empty_schedule(self) -> None:
        sol = GanttSolution()
        assert sol.entries_for_resource("r1") == ()


# ==================== GanttSolution utilization tests ====================


class TestGanttSolutionUtilization:
    """average_utilization, peak_utilization, idle_resources tests."""

    def test_average_utilization_no_resources(self) -> None:
        sol = GanttSolution()
        assert sol.average_utilization == pytest.approx(0.0)

    def test_average_utilization_single(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(_make_utilization("r1", 10.0, 5.0),)
        )
        assert sol.average_utilization == pytest.approx(0.5)

    def test_average_utilization_multiple(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(
                _make_utilization("r1", 10.0, 5.0),
                _make_utilization("r2", 10.0, 8.0),
            )
        )
        assert sol.average_utilization == pytest.approx(0.65)

    def test_peak_utilization_no_resources(self) -> None:
        sol = GanttSolution()
        assert sol.peak_utilization == pytest.approx(0.0)

    def test_peak_utilization_single(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(_make_utilization("r1", 10.0, 7.0),)
        )
        assert sol.peak_utilization == pytest.approx(0.7)

    def test_peak_utilization_multiple(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(
                _make_utilization("r1", 10.0, 3.0),
                _make_utilization("r2", 10.0, 9.0),
            )
        )
        assert sol.peak_utilization == pytest.approx(0.9)

    def test_idle_resources_none(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(
                _make_utilization("r1", 10.0, 5.0),
                _make_utilization("r2", 10.0, 3.0),
            )
        )
        assert sol.idle_resources == ()

    def test_idle_resources_some(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(
                _make_utilization("r1", 10.0, 5.0),
                _make_utilization("r2", 10.0, 0.0),
                _make_utilization("r3", 10.0, 0.0),
            )
        )
        assert sol.idle_resources == ("r2", "r3")

    def test_utilization_for_found(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(_make_utilization("r1", 10.0, 5.0),)
        )
        u = sol.utilization_for("r1")
        assert u is not None
        assert u.utilization_rate == pytest.approx(0.5)

    def test_utilization_for_not_found(self) -> None:
        sol = GanttSolution(
            resource_utilizations=(_make_utilization("r1", 10.0, 5.0),)
        )
        assert sol.utilization_for("r99") is None
