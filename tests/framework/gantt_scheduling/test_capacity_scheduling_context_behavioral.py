"""CapacitySchedulingContext behavioral tests.

Covers context registration, queries, constraint building, and config.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.capacity_scheduling_context import (
    CapacitySchedulingContext,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
    Capacity as SlotCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aggregation import (
    CapacitySchedulingAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_model import (
    CapacitySchedulingModel,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_modeling_config import (
    CapacitySchedulingModelingConfig,
)

# ==================== Stub objects ====================


@dataclass(frozen=True)
class _StubAssignment:
    work_item_key: str
    assignment_amount: float = 0.0


@dataclass(frozen=True)
class _StubLoad:
    capacity_slot_key: str
    load_amount: float = 0.0


# ==================== CapacitySchedulingContext tests ====================


class TestCapacitySchedulingContextDefaults:
    """CapacitySchedulingContext default construction tests."""

    def test_default_construction(self) -> None:
        ctx = CapacitySchedulingContext()
        assert isinstance(ctx.aggregation, CapacitySchedulingAggregation)
        assert isinstance(ctx.model, CapacitySchedulingModel)

    def test_frozen(self) -> None:
        ctx = CapacitySchedulingContext()
        with pytest.raises(AttributeError):
            ctx.model = CapacitySchedulingModel()  # type: ignore[misc]


class TestCapacitySchedulingContextRegistration:
    """CapacitySchedulingContext immutable registration methods."""

    def test_register_assignment_returns_new(self) -> None:
        ctx = CapacitySchedulingContext()
        a = _StubAssignment(work_item_key="w1")
        new_ctx = ctx.register_assignment(a)
        assert new_ctx is not ctx
        assert len(new_ctx.aggregation.work_item_keys) == 1
        assert len(ctx.aggregation.work_item_keys) == 0

    def test_register_capacity_returns_new(self) -> None:
        ctx = CapacitySchedulingContext()
        c = SlotCapacity(capacity_slot_key="s1")
        new_ctx = ctx.register_capacity(c)
        assert new_ctx is not ctx
        assert len(new_ctx.aggregation.capacities) == 1

    def test_register_load_returns_new(self) -> None:
        ctx = CapacitySchedulingContext()
        load = _StubLoad(capacity_slot_key="s1", load_amount=5.0)
        new_ctx = ctx.register_load(load)
        assert new_ctx is not ctx


class TestCapacitySchedulingContextQueries:
    """CapacitySchedulingContext query methods."""

    def test_get_capacity_found(self) -> None:
        c = SlotCapacity(capacity_slot_key="s1", max_capacity=100.0, used_capacity=20.0)
        ctx = CapacitySchedulingContext()
        ctx = ctx.register_capacity(c)
        result = ctx.get_capacity("s1")
        assert result is c

    def test_get_capacity_not_found(self) -> None:
        ctx = CapacitySchedulingContext()
        assert ctx.get_capacity("s1") is None

    def test_remaining_capacity_found(self) -> None:
        c = SlotCapacity(capacity_slot_key="s1", max_capacity=100.0, used_capacity=40.0)
        ctx = CapacitySchedulingContext()
        ctx = ctx.register_capacity(c)
        assert ctx.remaining_capacity("s1") == pytest.approx(60.0)

    def test_remaining_capacity_not_found(self) -> None:
        ctx = CapacitySchedulingContext()
        assert ctx.remaining_capacity("s1") == pytest.approx(0.0)


class TestCapacitySchedulingContextConstraints:
    """CapacitySchedulingContext constraint building."""

    def test_build_capacity_constraints(self) -> None:
        ctx = CapacitySchedulingContext()
        c = SlotCapacity(capacity_slot_key="s1")
        ctx = ctx.register_capacity(c)
        result = ctx.build_capacity_constraints()
        assert isinstance(result, tuple)

    def test_check_demand_feasibility(self) -> None:
        ctx = CapacitySchedulingContext()
        result = ctx.check_demand_feasibility()
        assert isinstance(result, bool)


class TestCapacitySchedulingContextConfig:
    """CapacitySchedulingContext with_config."""

    def test_with_config_returns_new(self) -> None:
        ctx = CapacitySchedulingContext()
        config = CapacitySchedulingModelingConfig()
        new_ctx = ctx.with_config(config)
        assert new_ctx is not ctx


# ==================== CapacitySchedulingAggregation extended tests ====================


class TestCapacitySchedulingAggregationExtended:
    """Additional CapacitySchedulingAggregation behavioral tests."""

    def test_work_item_keys_deduplication(self) -> None:
        a1 = _StubAssignment(work_item_key="w1")
        a2 = _StubAssignment(work_item_key="w1")
        a3 = _StubAssignment(work_item_key="w2")
        agg = CapacitySchedulingAggregation(_assignments=(a1, a2, a3))
        assert agg.work_item_keys == ("w1", "w2")

    def test_assignments_for_work_item(self) -> None:
        a1 = _StubAssignment(work_item_key="w1", assignment_amount=5.0)
        a2 = _StubAssignment(work_item_key="w1", assignment_amount=3.0)
        a3 = _StubAssignment(work_item_key="w2", assignment_amount=10.0)
        agg = CapacitySchedulingAggregation(_assignments=(a1, a2, a3))
        result = agg.assignments_for_work_item("w1")
        assert len(result) == 2

    def test_total_load_for_slot(self) -> None:
        l1 = _StubLoad(capacity_slot_key="s1", load_amount=5.0)
        l2 = _StubLoad(capacity_slot_key="s1", load_amount=3.0)
        l3 = _StubLoad(capacity_slot_key="s2", load_amount=10.0)
        agg = CapacitySchedulingAggregation(_loads=(l1, l2, l3))
        assert agg.total_load_for_slot("s1") == pytest.approx(8.0)
        assert agg.total_load_for_slot("s2") == pytest.approx(10.0)
        assert agg.total_load_for_slot("s3") == pytest.approx(0.0)

    def test_get_capacity_found(self) -> None:
        c = SlotCapacity(capacity_slot_key="s1", max_capacity=100.0, used_capacity=50.0)
        agg = CapacitySchedulingAggregation(_capacities=(c,))
        assert agg.get_capacity("s1") is c

    def test_get_capacity_not_found(self) -> None:
        agg = CapacitySchedulingAggregation()
        assert agg.get_capacity("s1") is None

    def test_is_valid_empty_name(self) -> None:
        agg = CapacitySchedulingAggregation(name="")
        assert agg.is_valid is False
