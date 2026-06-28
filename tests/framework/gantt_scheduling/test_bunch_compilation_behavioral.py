"""BunchCompilationContext and BunchCompilationAggregation behavioral tests.

Covers context registration, queries, constraint building, and
aggregation mutation (immutable copies), lookups, and computations.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.bunch_compilation_context import (
    BunchCompilationContext,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
    BunchCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_model import (
    BunchCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_modeling_config import (
    BunchCompilationModelingConfig,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.capacity import (
    Capacity as BunchCapacity,
)

# ==================== Stub objects for context tests ====================


@dataclass(frozen=True)
class _StubAssignment:
    item_key: str
    bunch_key: str
    demand: float = 0.0


@dataclass(frozen=True)
class _StubLoad:
    bunch_key: str
    load_amount: float = 0.0


# ==================== BunchCompilationAggregation tests ====================


class TestBunchCompilationAggregationDefaults:
    """BunchCompilationAggregation default state tests."""

    def test_default_name(self) -> None:
        agg = BunchCompilationAggregation()
        assert agg.name == "bunch_compilation_aggregation"

    def test_default_is_valid(self) -> None:
        agg = BunchCompilationAggregation()
        assert agg.is_valid is True

    def test_default_empty(self) -> None:
        agg = BunchCompilationAggregation()
        assert agg.assignments == ()
        assert agg.capacities == ()
        assert agg.item_keys == ()
        assert agg.bunch_keys == ()


class TestBunchCompilationAggregationMutation:
    """BunchCompilationAggregation immutable with_* methods."""

    def test_with_assignment(self) -> None:
        agg = BunchCompilationAggregation()
        a = _StubAssignment(item_key="i1", bunch_key="b1")
        new_agg = agg.with_assignment(a)
        assert len(new_agg.assignments) == 1
        assert len(agg.assignments) == 0  # original unchanged

    def test_with_capacity(self) -> None:
        agg = BunchCompilationAggregation()
        c = BunchCapacity(bunch_key="b1")
        new_agg = agg.with_capacity(c)
        assert len(new_agg.capacities) == 1
        assert len(agg.capacities) == 0

    def test_with_load(self) -> None:
        agg = BunchCompilationAggregation()
        load = _StubLoad(bunch_key="b1", load_amount=5.0)
        new_agg = agg.with_load(load)
        # loads are stored internally
        assert agg is not new_agg

    def test_frozen(self) -> None:
        agg = BunchCompilationAggregation()
        with pytest.raises(AttributeError):
            agg.name = "x"  # type: ignore[misc]


class TestBunchCompilationAggregationQueries:
    """BunchCompilationAggregation query methods."""

    def test_item_keys(self) -> None:
        agg = BunchCompilationAggregation(
            _items=("i1", "i2", "i3"),
        )
        assert agg.item_keys == ("i1", "i2", "i3")

    def test_bunch_keys_deduplication(self) -> None:
        a1 = _StubAssignment(item_key="i1", bunch_key="b1")
        a2 = _StubAssignment(item_key="i2", bunch_key="b1")
        a3 = _StubAssignment(item_key="i3", bunch_key="b2")
        agg = BunchCompilationAggregation(_assignments=(a1, a2, a3))
        assert agg.bunch_keys == ("b1", "b2")

    def test_get_assignment_found(self) -> None:
        a = _StubAssignment(item_key="i1", bunch_key="b1")
        agg = BunchCompilationAggregation(_assignments=(a,))
        result = agg.get_assignment(item_key="i1", bunch_key="b1")
        assert result is a

    def test_get_assignment_not_found(self) -> None:
        a = _StubAssignment(item_key="i1", bunch_key="b1")
        agg = BunchCompilationAggregation(_assignments=(a,))
        assert agg.get_assignment(item_key="i2", bunch_key="b1") is None
        assert agg.get_assignment(item_key="i1", bunch_key="b2") is None

    def test_assignments_for_item(self) -> None:
        a1 = _StubAssignment(item_key="i1", bunch_key="b1")
        a2 = _StubAssignment(item_key="i1", bunch_key="b2")
        a3 = _StubAssignment(item_key="i2", bunch_key="b1")
        agg = BunchCompilationAggregation(_assignments=(a1, a2, a3))
        result = agg.assignments_for_item("i1")
        assert len(result) == 2

    def test_assignments_for_item_empty(self) -> None:
        agg = BunchCompilationAggregation()
        assert agg.assignments_for_item("i1") == ()

    def test_get_capacity_found(self) -> None:
        c = BunchCapacity(bunch_key="b1", max_capacity=100.0, used_capacity=50.0)
        agg = BunchCompilationAggregation(_capacities=(c,))
        result = agg.get_capacity("b1")
        assert result is c
        assert result.remaining_capacity == pytest.approx(50.0)

    def test_get_capacity_not_found(self) -> None:
        agg = BunchCompilationAggregation()
        assert agg.get_capacity("b1") is None

    def test_total_demand_for_bunch(self) -> None:
        a1 = _StubAssignment(item_key="i1", bunch_key="b1", demand=5.0)
        a2 = _StubAssignment(item_key="i2", bunch_key="b1", demand=3.0)
        a3 = _StubAssignment(item_key="i3", bunch_key="b2", demand=10.0)
        agg = BunchCompilationAggregation(_assignments=(a1, a2, a3))
        assert agg.total_demand_for_bunch("b1") == pytest.approx(8.0)
        assert agg.total_demand_for_bunch("b2") == pytest.approx(10.0)
        assert agg.total_demand_for_bunch("b3") == pytest.approx(0.0)

    def test_is_valid_empty_name(self) -> None:
        agg = BunchCompilationAggregation(name="")
        assert agg.is_valid is False


# ==================== BunchCompilationContext tests ====================


class TestBunchCompilationContextDefaults:
    """BunchCompilationContext default construction tests."""

    def test_default_construction(self) -> None:
        ctx = BunchCompilationContext()
        assert isinstance(ctx.aggregation, BunchCompilationAggregation)
        assert isinstance(ctx.model, BunchCompilationModel)

    def test_frozen(self) -> None:
        ctx = BunchCompilationContext()
        with pytest.raises(AttributeError):
            ctx.model = BunchCompilationModel()  # type: ignore[misc]


class TestBunchCompilationContextRegistration:
    """BunchCompilationContext immutable registration methods."""

    def test_register_assignment_returns_new(self) -> None:
        ctx = BunchCompilationContext()
        a = _StubAssignment(item_key="i1", bunch_key="b1")
        new_ctx = ctx.register_assignment(a)
        assert new_ctx is not ctx
        assert len(new_ctx.aggregation.assignments) == 1
        assert len(ctx.aggregation.assignments) == 0

    def test_register_capacity_returns_new(self) -> None:
        ctx = BunchCompilationContext()
        c = BunchCapacity(bunch_key="b1")
        new_ctx = ctx.register_capacity(c)
        assert new_ctx is not ctx
        assert len(new_ctx.aggregation.capacities) == 1

    def test_register_load_returns_new(self) -> None:
        ctx = BunchCompilationContext()
        load = _StubLoad(bunch_key="b1")
        new_ctx = ctx.register_load(load)
        assert new_ctx is not ctx


class TestBunchCompilationContextQueries:
    """BunchCompilationContext query methods."""

    def test_get_assignment(self) -> None:
        a = _StubAssignment(item_key="i1", bunch_key="b1")
        ctx = BunchCompilationContext()
        ctx = ctx.register_assignment(a)
        result = ctx.get_assignment(item_key="i1", bunch_key="b1")
        assert result is a

    def test_get_assignment_not_found(self) -> None:
        ctx = BunchCompilationContext()
        assert ctx.get_assignment(item_key="i1", bunch_key="b1") is None

    def test_assignments_for_item(self) -> None:
        a1 = _StubAssignment(item_key="i1", bunch_key="b1")
        a2 = _StubAssignment(item_key="i1", bunch_key="b2")
        ctx = BunchCompilationContext()
        ctx = ctx.register_assignment(a1)
        ctx = ctx.register_assignment(a2)
        result = ctx.assignments_for_item("i1")
        assert len(result) == 2

    def test_remaining_capacity_found(self) -> None:
        c = BunchCapacity(bunch_key="b1", max_capacity=100.0, used_capacity=50.0)
        ctx = BunchCompilationContext()
        ctx = ctx.register_capacity(c)
        assert ctx.remaining_capacity("b1") == pytest.approx(50.0)

    def test_remaining_capacity_not_found(self) -> None:
        ctx = BunchCompilationContext()
        assert ctx.remaining_capacity("b1") == pytest.approx(0.0)


class TestBunchCompilationContextConstraints:
    """BunchCompilationContext constraint building."""

    def test_build_capacity_constraints(self) -> None:
        ctx = BunchCompilationContext()
        c = BunchCapacity(bunch_key="b1")
        ctx = ctx.register_capacity(c)
        result = ctx.build_capacity_constraints()
        assert isinstance(result, tuple)

    def test_check_demand_feasibility(self) -> None:
        ctx = BunchCompilationContext()
        result = ctx.check_demand_feasibility()
        assert isinstance(result, bool)


class TestBunchCompilationContextConfig:
    """BunchCompilationContext with_config."""

    def test_with_config_returns_new(self) -> None:
        ctx = BunchCompilationContext()
        config = BunchCompilationModelingConfig()
        new_ctx = ctx.with_config(config)
        assert new_ctx is not ctx
