"""Task compilation constraint behavioral tests.

Covers setup_time_constraint, task_tail_assignment_constraint,
resource_capacity_constraint, and sequence_dependent_setup_constraint
with stub adapters that exercise real logic.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_capacity_constraint import (
    ResourceCapacityConstraint,
    ResourceCapacityData,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.sequence_dependent_setup_constraint import (
    SequenceDependentSetupConstraint,
    SetupTimeData,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.setup_time_constraint import (
    SetupTimeConstraint,
    SetupTimePair,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_tail_assignment_constraint import (
    TailAssignmentData,
    TaskTailAssignmentConstraint,
)

# ==================== Stub adapters ====================


@dataclass(frozen=True)
class _StubTask:
    task_key: str


@dataclass(frozen=True)
class _StubCapRecord:
    resource_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float


@dataclass(frozen=True)
class _StubDemand:
    resource_key: str
    task_key: str
    demand_amount: float


@dataclass(frozen=True)
class _StubAdjacentPair:
    predecessor_key: str
    successor_key: str


@dataclass
class _StubAdapter:
    """Stub adapter for testing constraint logic."""
    tasks: tuple[_StubTask, ...] = ()
    _setup_durations: dict[str, float] | None = None
    _task_start_times: dict[str, float] | None = None
    _earliest_available: dict[str, float] | None = None
    _tail_resources: dict[str, str | None] | None = None
    _tail_required: dict[str, float] | None = None
    _tail_assigned: dict[str, float] | None = None
    resource_capacities: tuple[_StubCapRecord, ...] = ()
    _demands_in_window: dict[tuple[str, float, float], tuple[_StubDemand, ...]] | None = None
    adjacent_task_pairs: tuple[_StubAdjacentPair, ...] = ()
    _setup_times_between: dict[tuple[str, str], float] | None = None
    _task_end_times: dict[str, float] | None = None

    def setup_duration(self, task_key: str) -> float:
        if self._setup_durations is not None:
            return self._setup_durations.get(task_key, 0.0)
        return 0.0

    def task_start_time(self, task_key: str) -> float:
        if self._task_start_times is not None:
            return self._task_start_times.get(task_key, 0.0)
        return 0.0

    def earliest_available(self, task_key: str) -> float:
        if self._earliest_available is not None:
            return self._earliest_available.get(task_key, 0.0)
        return 0.0

    def tail_resource(self, task_key: str) -> str | None:
        if self._tail_resources is not None:
            return self._tail_resources.get(task_key, None)
        return None

    def tail_required_amount(self, task_key: str) -> float:
        if self._tail_required is not None:
            return self._tail_required.get(task_key, 0.0)
        return 0.0

    def tail_assigned_amount(self, task_key: str) -> float:
        if self._tail_assigned is not None:
            return self._tail_assigned.get(task_key, 0.0)
        return 0.0

    def demands_in_window(
        self, resource_key: str, window_start: float, window_end: float
    ) -> tuple[_StubDemand, ...]:
        if self._demands_in_window is not None:
            return self._demands_in_window.get((resource_key, window_start, window_end), ())
        return ()

    def setup_time_between(self, pred: str, succ: str) -> float:
        if self._setup_times_between is not None:
            return self._setup_times_between.get((pred, succ), 0.0)
        return 0.0

    def task_end_time(self, task_key: str) -> float:
        if self._task_end_times is not None:
            return self._task_end_times.get(task_key, 0.0)
        return 0.0


# ==================== SetupTimeConstraint tests ====================


class TestSetupTimePair:
    """SetupTimePair behavioral tests."""

    def test_construction(self) -> None:
        pair = SetupTimePair(
            task_key="t1", setup_duration=2.0, start_time=3.0, end_time=5.0, is_satisfied=True
        )
        assert pair.task_key == "t1"
        assert pair.setup_duration == pytest.approx(2.0)
        assert pair.is_satisfied is True


class TestSetupTimeConstraint:
    """SetupTimeConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = SetupTimeConstraint()
        assert c.constraint_name("t1") == "setup_time_t1"

    def test_constraint_name_custom_prefix(self) -> None:
        c = SetupTimeConstraint(constraint_name_prefix="custom")
        assert c.constraint_name("t1") == "custom_t1"

    def test_build_constraints_no_setup(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(tasks=(_StubTask("t1"),), _setup_durations={"t1": 0.0})
        result = c.build_constraints(adapter)
        assert result == ()

    def test_build_constraints_satisfied(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 2.0},
            _task_start_times={"t1": 5.0},
            _earliest_available={"t1": 3.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].task_key == "t1"
        assert result[0].setup_duration == pytest.approx(2.0)
        assert result[0].start_time == pytest.approx(3.0)
        assert result[0].end_time == pytest.approx(5.0)
        assert result[0].is_satisfied is True

    def test_build_constraints_violated(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 3.0},
            _task_start_times={"t1": 5.0},
            _earliest_available={"t1": 4.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].is_satisfied is False

    def test_is_satisfied_true(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 2.0},
            _task_start_times={"t1": 5.0},
            _earliest_available={"t1": 0.0},
        )
        assert c.is_satisfied(adapter) is True

    def test_is_satisfied_false(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 5.0},
            _task_start_times={"t1": 3.0},
            _earliest_available={"t1": 2.0},
        )
        assert c.is_satisfied(adapter) is False

    def test_violations_empty(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 2.0},
            _task_start_times={"t1": 5.0},
            _earliest_available={"t1": 0.0},
        )
        assert c.violations(adapter) == ()

    def test_violations_found(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _setup_durations={"t1": 5.0},
            _task_start_times={"t1": 3.0},
            _earliest_available={"t1": 2.0},
        )
        viols = c.violations(adapter)
        assert len(viols) == 1
        assert viols[0].task_key == "t1"

    def test_multiple_tasks(self) -> None:
        c = SetupTimeConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"), _StubTask("t2")),
            _setup_durations={"t1": 2.0, "t2": 0.0},
            _task_start_times={"t1": 5.0},
            _earliest_available={"t1": 0.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1  # t2 has setup=0, skipped


# ==================== TaskTailAssignmentConstraint tests ====================


class TestTailAssignmentData:
    """TailAssignmentData behavioral tests."""

    def test_construction(self) -> None:
        data = TailAssignmentData(
            task_key="t1", tail_resource_key="r1",
            is_assigned=True, assigned_amount=5.0, required_amount=5.0
        )
        assert data.task_key == "t1"
        assert data.is_assigned is True


class TestTaskTailAssignmentConstraint:
    """TaskTailAssignmentConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = TaskTailAssignmentConstraint()
        assert c.constraint_name("t1") == "tail_assignment_t1"

    def test_build_constraints_no_tail(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(tasks=(_StubTask("t1"),), _tail_resources={"t1": None})
        result = c.build_constraints(adapter)
        assert result == ()

    def test_build_constraints_satisfied(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 5.0},
            _tail_assigned={"t1": 5.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].is_assigned is True

    def test_build_constraints_violated(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 10.0},
            _tail_assigned={"t1": 3.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].is_assigned is False

    def test_is_satisfied_true(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 5.0},
            _tail_assigned={"t1": 5.0},
        )
        assert c.is_satisfied(adapter) is True

    def test_is_satisfied_false(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 10.0},
            _tail_assigned={"t1": 2.0},
        )
        assert c.is_satisfied(adapter) is False

    def test_violations_empty(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 5.0},
            _tail_assigned={"t1": 5.0},
        )
        assert c.violations(adapter) == ()

    def test_violations_found(self) -> None:
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 10.0},
            _tail_assigned={"t1": 2.0},
        )
        viols = c.violations(adapter)
        assert len(viols) == 1

    def test_boundary_assigned_equals_required_minus_epsilon(self) -> None:
        """assigned = required - 1e-10 should still be satisfied (tolerance is 1e-9)."""
        c = TaskTailAssignmentConstraint()
        adapter = _StubAdapter(
            tasks=(_StubTask("t1"),),
            _tail_resources={"t1": "r1"},
            _tail_required={"t1": 10.0},
            _tail_assigned={"t1": 10.0 - 1e-10},
        )
        result = c.build_constraints(adapter)
        assert result[0].is_assigned is True


# ==================== ResourceCapacityConstraint tests ====================


class TestResourceCapacityData:
    """ResourceCapacityData behavioral tests."""

    def test_remaining_capacity(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=100.0, used_capacity=60.0
        )
        assert data.remaining_capacity == pytest.approx(40.0)

    def test_remaining_capacity_clamped_at_zero(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=50.0, used_capacity=80.0
        )
        assert data.remaining_capacity == pytest.approx(0.0)

    def test_utilization_ratio_normal(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=100.0, used_capacity=70.0
        )
        assert data.utilization_ratio == pytest.approx(0.7)

    def test_utilization_ratio_capped_at_one(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=50.0, used_capacity=80.0
        )
        assert data.utilization_ratio == pytest.approx(1.0)

    def test_utilization_ratio_zero_capacity(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=0.0, used_capacity=0.0
        )
        assert data.utilization_ratio == pytest.approx(0.0)

    def test_is_over_capacity_true(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=50.0, used_capacity=80.0
        )
        assert data.is_over_capacity is True

    def test_is_over_capacity_false(self) -> None:
        data = ResourceCapacityData(
            resource_key="r1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=100.0, used_capacity=50.0
        )
        assert data.is_over_capacity is False


class TestResourceCapacityConstraint:
    """ResourceCapacityConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = ResourceCapacityConstraint()
        name = c.constraint_name(resource_key="r1", window_start=0.0, window_end=10.0)
        assert name == "resource_capacity_r1_0.0_10.0"

    def test_build_constraints_within_capacity(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 100.0)
        demand = _StubDemand("r1", "t1", 40.0)
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): (demand,)},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].used_capacity == pytest.approx(40.0)
        assert result[0].is_over_capacity is False

    def test_build_constraints_over_capacity(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 50.0)
        demands = (_StubDemand("r1", "t1", 30.0), _StubDemand("r1", "t2", 30.0))
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): demands},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].used_capacity == pytest.approx(60.0)
        assert result[0].is_over_capacity is True

    def test_is_satisfied_true(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 100.0)
        demand = _StubDemand("r1", "t1", 30.0)
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): (demand,)},
        )
        assert c.is_satisfied(adapter) is True

    def test_is_satisfied_false(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 50.0)
        demand = _StubDemand("r1", "t1", 80.0)
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): (demand,)},
        )
        assert c.is_satisfied(adapter) is False

    def test_violations_found(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 50.0)
        demand = _StubDemand("r1", "t1", 80.0)
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): (demand,)},
        )
        viols = c.violations(adapter)
        assert len(viols) == 1

    def test_violations_empty(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 100.0)
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={},
        )
        viols = c.violations(adapter)
        assert len(viols) == 0

    def test_build_constraints_multiple_demands(self) -> None:
        c = ResourceCapacityConstraint()
        cap = _StubCapRecord("r1", 0.0, 10.0, 100.0)
        demands = (_StubDemand("r1", "t1", 20.0), _StubDemand("r1", "t2", 30.0))
        adapter = _StubAdapter(
            resource_capacities=(cap,),
            _demands_in_window={("r1", 0.0, 10.0): demands},
        )
        result = c.build_constraints(adapter)
        assert result[0].used_capacity == pytest.approx(50.0)


# ==================== SequenceDependentSetupConstraint tests ====================


class TestSetupTimeData:
    """SetupTimeData behavioral tests."""

    def test_construction(self) -> None:
        data = SetupTimeData(
            predecessor_key="t1", successor_key="t2",
            required_setup=3.0, actual_gap=5.0, is_satisfied=True
        )
        assert data.predecessor_key == "t1"
        assert data.is_satisfied is True


class TestSequenceDependentSetupConstraint:
    """SequenceDependentSetupConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = SequenceDependentSetupConstraint()
        name = c.constraint_name(predecessor_key="t1", successor_key="t2")
        assert name == "seq_setup_t1_t2"

    def test_build_constraints_satisfied(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 2.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 8.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].actual_gap == pytest.approx(3.0)
        assert result[0].is_satisfied is True

    def test_build_constraints_violated(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 5.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 7.0},
        )
        result = c.build_constraints(adapter)
        assert len(result) == 1
        assert result[0].actual_gap == pytest.approx(2.0)
        assert result[0].is_satisfied is False

    def test_build_constraints_exact_gap_satisfied(self) -> None:
        """Gap equals required setup should be satisfied (tolerance 1e-9)."""
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 3.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 8.0},
        )
        result = c.build_constraints(adapter)
        assert result[0].is_satisfied is True

    def test_is_satisfied_true(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 2.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 10.0},
        )
        assert c.is_satisfied(adapter) is True

    def test_is_satisfied_false(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 5.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 6.0},
        )
        assert c.is_satisfied(adapter) is False

    def test_violations_empty(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 2.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 10.0},
        )
        assert c.violations(adapter) == ()

    def test_violations_found(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(
            adjacent_task_pairs=(_StubAdjacentPair("t1", "t2"),),
            _setup_times_between={("t1", "t2"): 5.0},
            _task_end_times={"t1": 5.0},
            _task_start_times={"t2": 6.0},
        )
        viols = c.violations(adapter)
        assert len(viols) == 1

    def test_no_pairs(self) -> None:
        c = SequenceDependentSetupConstraint()
        adapter = _StubAdapter(adjacent_task_pairs=())
        assert c.is_satisfied(adapter) is True
        assert c.violations(adapter) == ()
