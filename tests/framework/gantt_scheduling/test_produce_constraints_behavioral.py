"""Produce constraint behavioral tests.

Covers ProduceCapacityConstraint, ProduceBatchOrderConstraint,
and ProduceOrderConstraint with stub aggregations.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_order_constraint import (
    BatchOrderPair,
    ProduceBatchOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_capacity_constraint import (
    ProduceCapacityConstraint,
    ProduceCapacityData,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_order_constraint import (
    ProduceOrderConstraint,
    ProduceOrderPair,
)

# ==================== Stub aggregation for produce constraints ====================


@dataclass(frozen=True)
class _StubCap:
    produce_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float


@dataclass(frozen=True)
class _StubDemand:
    produce_key: str
    time_window_start: float
    time_window_end: float
    demand_amount: float


@dataclass(frozen=True)
class _StubAssignment:
    item_key: str = ""
    batch_key: str = ""
    start_time: float = 0.0
    end_time: float = 0.0


@dataclass(frozen=True)
class _StubOrderPair:
    predecessor_key: str
    successor_key: str


@dataclass(frozen=True)
class _StubBatchOrderPair:
    predecessor_key: str
    successor_key: str


@dataclass(frozen=True)
class _StubProduceAggregation:
    """Stub aggregation for produce constraint tests."""
    capacities: tuple[_StubCap, ...] = ()
    demands: tuple[_StubDemand, ...] = ()
    order_pairs: tuple[_StubOrderPair, ...] = ()
    batch_order_pairs: tuple[_StubBatchOrderPair, ...] = ()
    _assignments: tuple[_StubAssignment, ...] = ()

    def assignments_for_item(self, item_key: str) -> tuple[_StubAssignment, ...]:
        return tuple(a for a in self._assignments if a.item_key == item_key)

    def assignments_for_batch(self, batch_key: str) -> tuple[_StubAssignment, ...]:
        return tuple(a for a in self._assignments if a.batch_key == batch_key)


# ==================== ProduceCapacityData tests ====================


class TestProduceCapacityData:
    """ProduceCapacityData behavioral tests."""

    def test_remaining_capacity(self) -> None:
        data = ProduceCapacityData(
            produce_key="p1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=100.0, used_capacity=70.0
        )
        assert data.remaining_capacity == pytest.approx(30.0)

    def test_remaining_capacity_clamped(self) -> None:
        data = ProduceCapacityData(
            produce_key="p1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=50.0, used_capacity=80.0
        )
        assert data.remaining_capacity == pytest.approx(0.0)

    def test_is_over_capacity_true(self) -> None:
        data = ProduceCapacityData(
            produce_key="p1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=50.0, used_capacity=60.0
        )
        assert data.is_over_capacity is True

    def test_is_over_capacity_false(self) -> None:
        data = ProduceCapacityData(
            produce_key="p1", time_window_start=0.0, time_window_end=10.0,
            max_capacity=100.0, used_capacity=40.0
        )
        assert data.is_over_capacity is False


# ==================== ProduceCapacityConstraint tests ====================


class TestProduceCapacityConstraint:
    """ProduceCapacityConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = ProduceCapacityConstraint()
        name = c.constraint_name(produce_key="p1", window_start=0.0, window_end=10.0)
        assert name == "produce_capacity_p1_0.0_10.0"

    def test_build_constraints_within_capacity(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 100.0),),
            demands=(_StubDemand("p1", 2.0, 8.0, 50.0),),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].used_capacity == pytest.approx(50.0)
        assert result[0].is_over_capacity is False

    def test_build_constraints_over_capacity(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 50.0),),
            demands=(_StubDemand("p1", 2.0, 8.0, 60.0),),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].is_over_capacity is True

    def test_build_constraints_no_demands(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 100.0),),
            demands=(),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].used_capacity == pytest.approx(0.0)

    def test_build_constraints_no_capacities(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation()
        result = c.build_constraints(agg)
        assert result == ()

    def test_is_satisfied_true(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 100.0),),
            demands=(_StubDemand("p1", 2.0, 8.0, 50.0),),
        )
        assert c.is_satisfied(agg) is True

    def test_is_satisfied_false(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 50.0),),
            demands=(_StubDemand("p1", 2.0, 8.0, 80.0),),
        )
        assert c.is_satisfied(agg) is False

    def test_violations_found(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 50.0),),
            demands=(_StubDemand("p1", 2.0, 8.0, 80.0),),
        )
        viols = c.violations(agg)
        assert len(viols) == 1

    def test_violations_empty(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 0.0, 10.0, 100.0),),
            demands=(),
        )
        assert c.violations(agg) == ()

    def test_overlapping_demands_filter(self) -> None:
        """Test _overlapping_demands filters by produce_key and time overlap."""
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(_StubCap("p1", 5.0, 15.0, 100.0),),
            demands=(
                _StubDemand("p1", 0.0, 6.0, 10.0),   # overlaps [5,15]
                _StubDemand("p1", 14.0, 20.0, 20.0),  # overlaps [5,15]
                _StubDemand("p1", 16.0, 20.0, 30.0),  # no overlap
                _StubDemand("p2", 0.0, 20.0, 40.0),   # different produce
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        # Should sum only overlapping demands: 10 + 20 = 30
        assert result[0].used_capacity == pytest.approx(30.0)

    def test_multiple_capacities(self) -> None:
        c = ProduceCapacityConstraint()
        agg = _StubProduceAggregation(
            capacities=(
                _StubCap("p1", 0.0, 10.0, 100.0),
                _StubCap("p2", 0.0, 10.0, 200.0),
            ),
            demands=(
                _StubDemand("p1", 2.0, 8.0, 40.0),
                _StubDemand("p2", 1.0, 9.0, 80.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 2


# ==================== ProduceBatchOrderConstraint tests ====================


class TestBatchOrderPair:
    """BatchOrderPair behavioral tests."""

    def test_construction(self) -> None:
        pair = BatchOrderPair(
            predecessor_key="b1", successor_key="b2",
            is_satisfied=True, predecessor_end=5.0, successor_start=6.0
        )
        assert pair.predecessor_key == "b1"
        assert pair.is_satisfied is True


class TestProduceBatchOrderConstraint:
    """ProduceBatchOrderConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = ProduceBatchOrderConstraint()
        name = c.constraint_name(predecessor_key="b1", successor_key="b2")
        assert name == "produce_batch_order_b1_b2"

    def test_build_constraints_satisfied(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(
                _StubAssignment(batch_key="b1", start_time=0.0, end_time=5.0),
                _StubAssignment(batch_key="b2", start_time=6.0, end_time=10.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].is_satisfied is True
        assert result[0].predecessor_end == pytest.approx(5.0)
        assert result[0].successor_start == pytest.approx(6.0)

    def test_build_constraints_violated(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(
                _StubAssignment(batch_key="b1", start_time=0.0, end_time=8.0),
                _StubAssignment(batch_key="b2", start_time=5.0, end_time=10.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].is_satisfied is False

    def test_build_constraints_no_assignments(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        # pred_end = max(default=0.0), succ_start = min(default=inf)
        assert result[0].is_satisfied is True

    def test_is_satisfied_true(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(
                _StubAssignment(batch_key="b1", start_time=0.0, end_time=5.0),
                _StubAssignment(batch_key="b2", start_time=5.0, end_time=10.0),
            ),
        )
        assert c.is_satisfied(agg) is True

    def test_is_satisfied_false(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(
                _StubAssignment(batch_key="b1", start_time=0.0, end_time=8.0),
                _StubAssignment(batch_key="b2", start_time=5.0, end_time=10.0),
            ),
        )
        assert c.is_satisfied(agg) is False

    def test_violations_found(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(_StubBatchOrderPair("b1", "b2"),),
            _assignments=(
                _StubAssignment(batch_key="b1", start_time=0.0, end_time=8.0),
                _StubAssignment(batch_key="b2", start_time=5.0, end_time=10.0),
            ),
        )
        assert len(c.violations(agg)) == 1

    def test_violations_empty(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(batch_order_pairs=())
        assert c.violations(agg) == ()

    def test_multiple_pairs(self) -> None:
        c = ProduceBatchOrderConstraint()
        agg = _StubProduceAggregation(
            batch_order_pairs=(
                _StubBatchOrderPair("b1", "b2"),
                _StubBatchOrderPair("b2", "b3"),
            ),
            _assignments=(
                _StubAssignment(batch_key="b1", end_time=3.0),
                _StubAssignment(batch_key="b2", start_time=4.0, end_time=7.0),
                _StubAssignment(batch_key="b3", start_time=8.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 2
        assert result[0].is_satisfied is True
        assert result[1].is_satisfied is True


# ==================== ProduceOrderConstraint tests ====================


class TestProduceOrderPair:
    """ProduceOrderPair behavioral tests."""

    def test_construction(self) -> None:
        pair = ProduceOrderPair(
            predecessor_key="i1", successor_key="i2",
            is_satisfied=True, predecessor_end=5.0, successor_start=6.0
        )
        assert pair.predecessor_key == "i1"


class TestProduceOrderConstraint:
    """ProduceOrderConstraint behavioral tests."""

    def test_constraint_name(self) -> None:
        c = ProduceOrderConstraint()
        name = c.constraint_name(predecessor_key="i1", successor_key="i2")
        assert name == "produce_order_i1_i2"

    def test_build_constraints_satisfied(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(
                _StubAssignment(item_key="i1", start_time=0.0, end_time=5.0),
                _StubAssignment(item_key="i2", start_time=6.0, end_time=10.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].is_satisfied is True

    def test_build_constraints_violated(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(
                _StubAssignment(item_key="i1", start_time=0.0, end_time=8.0),
                _StubAssignment(item_key="i2", start_time=5.0, end_time=10.0),
            ),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].is_satisfied is False

    def test_build_constraints_no_assignments(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(),
        )
        result = c.build_constraints(agg)
        assert len(result) == 1
        # pred_end = max(default=0.0), succ_start = min(default=inf)
        assert result[0].is_satisfied is True

    def test_is_satisfied_true(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(
                _StubAssignment(item_key="i1", end_time=5.0),
                _StubAssignment(item_key="i2", start_time=5.0),
            ),
        )
        assert c.is_satisfied(agg) is True

    def test_is_satisfied_false(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(
                _StubAssignment(item_key="i1", end_time=8.0),
                _StubAssignment(item_key="i2", start_time=5.0),
            ),
        )
        assert c.is_satisfied(agg) is False

    def test_violations_found(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(
            order_pairs=(_StubOrderPair("i1", "i2"),),
            _assignments=(
                _StubAssignment(item_key="i1", end_time=8.0),
                _StubAssignment(item_key="i2", start_time=5.0),
            ),
        )
        assert len(c.violations(agg)) == 1

    def test_no_order_pairs(self) -> None:
        c = ProduceOrderConstraint()
        agg = _StubProduceAggregation(order_pairs=())
        assert c.is_satisfied(agg) is True
        assert c.violations(agg) == ()
