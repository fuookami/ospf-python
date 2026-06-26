"""束编组容量约束测试。

Bunch capacity constraint tests.

测试 BunchCapacityConstraint 的构造、约束名称生成、
约束构建、可行性和违规检测。
Tests BunchCapacityConstraint construction, constraint name
generation, constraint building, feasibility, and violations.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
    BunchCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.service.limits.bunch_capacity_constraint import (
    BunchCapacityConstraint,
)

# ── test helpers ───────────────────────────────────────────────


@dataclass(frozen=True)
class _FakeAssignment:
    """模拟分配记录。/ Fake assignment record."""

    item_key: str
    bunch_key: str
    demand: float


@dataclass(frozen=True)
class _FakeCapacity:
    """模拟容量记录。/ Fake capacity record."""

    bunch_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float


def _make_aggregation(
    assignments: list[_FakeAssignment],
    capacities: list[_FakeCapacity],
) -> BunchCompilationAggregation:
    """构建测试用聚合。/ Build test aggregation."""
    agg = BunchCompilationAggregation()
    for a in assignments:
        agg = agg.with_assignment(a)
    for c in capacities:
        agg = agg.with_capacity(c)
    return agg


# ── construction tests ─────────────────────────────────────────


class TestBunchCapacityConstraintConstruction:
    """构造测试。/ Construction tests."""

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        c = BunchCapacityConstraint()
        assert c.constraint_name_prefix == "bunch_capacity"

    def test_custom_prefix(self) -> None:
        """自定义前缀。/ Custom prefix."""
        c = BunchCapacityConstraint(
            constraint_name_prefix="bc",
        )
        assert c.constraint_name_prefix == "bc"

    def test_frozen(self) -> None:
        """不可变性。/ Frozen behavior."""
        c = BunchCapacityConstraint()
        import pytest

        with pytest.raises(AttributeError):
            c.constraint_name_prefix = "x"  # type: ignore[misc]


# ── constraint_name tests ──────────────────────────────────────


class TestBunchCapacityConstraintName:
    """约束名称测试。/ Constraint name tests."""

    def test_constraint_name(self) -> None:
        """生成约束名称。/ Generate constraint name."""
        c = BunchCapacityConstraint()
        name = c.constraint_name("bunch-1")
        assert name == "bunch_capacity_bunch-1"

    def test_constraint_name_custom_prefix(self) -> None:
        """自定义前缀约束名。/ Custom prefix name."""
        c = BunchCapacityConstraint(
            constraint_name_prefix="bc",
        )
        name = c.constraint_name("bunch-2")
        assert name == "bc_bunch-2"


# ── build_constraints tests ────────────────────────────────────


class TestBunchCapacityConstraintBuild:
    """构建约束测试。/ Build constraints tests."""

    def test_build_empty(self) -> None:
        """空聚合返回空约束。/ Empty aggregation returns empty."""
        c = BunchCapacityConstraint()
        agg = BunchCompilationAggregation()
        result = c.build_constraints(agg)
        assert result == ()

    def test_build_single(self) -> None:
        """单容量记录。/ Single capacity record."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        agg = _make_aggregation([], [cap])
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].bunch_key == "b1"
        assert result[0].max_capacity == 100.0

    def test_build_with_demand(self) -> None:
        """带需求的约束构建。/ Build with demand."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        a1 = _FakeAssignment(
            item_key="i1",
            bunch_key="b1",
            demand=30.0,
        )
        a2 = _FakeAssignment(
            item_key="i2",
            bunch_key="b1",
            demand=20.0,
        )
        agg = _make_aggregation([a1, a2], [cap])
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].used_capacity == 50.0


# ── is_feasible / violations tests ─────────────────────────────


class TestBunchCapacityConstraintFeasibility:
    """可行性测试。/ Feasibility tests."""

    def test_feasible(self) -> None:
        """可行聚合。/ Feasible aggregation."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        a = _FakeAssignment(
            item_key="i1",
            bunch_key="b1",
            demand=50.0,
        )
        agg = _make_aggregation([a], [cap])
        assert c.is_feasible(agg) is True

    def test_infeasible(self) -> None:
        """不可行聚合。/ Infeasible aggregation."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        a = _FakeAssignment(
            item_key="i1",
            bunch_key="b1",
            demand=50.0,
        )
        agg = _make_aggregation([a], [cap])
        assert c.is_feasible(agg) is False

    def test_violations_empty_when_feasible(self) -> None:
        """可行时无违反记录。/ No violations when feasible."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        a = _FakeAssignment(
            item_key="i1",
            bunch_key="b1",
            demand=50.0,
        )
        agg = _make_aggregation([a], [cap])
        assert c.violations(agg) == ()

    def test_violations_nonempty(self) -> None:
        """不可行时有违反记录。/ Has violations when infeasible."""
        c = BunchCapacityConstraint()
        cap = _FakeCapacity(
            bunch_key="b1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        a = _FakeAssignment(
            item_key="i1",
            bunch_key="b1",
            demand=50.0,
        )
        agg = _make_aggregation([a], [cap])
        violations = c.violations(agg)
        assert len(violations) == 1
        assert violations[0].used_capacity > violations[0].max_capacity

    def test_multiple_bunches(self) -> None:
        """多束编组约束。/ Multiple bunch constraints."""
        c = BunchCapacityConstraint()
        caps = [
            _FakeCapacity(
                bunch_key="b1",
                time_window_start=0.0,
                time_window_end=10.0,
                max_capacity=100.0,
            ),
            _FakeCapacity(
                bunch_key="b2",
                time_window_start=0.0,
                time_window_end=10.0,
                max_capacity=50.0,
            ),
        ]
        assignments = [
            _FakeAssignment(
                item_key="i1",
                bunch_key="b1",
                demand=30.0,
            ),
            _FakeAssignment(
                item_key="i2",
                bunch_key="b2",
                demand=60.0,
            ),
        ]
        agg = _make_aggregation(assignments, caps)
        result = c.build_constraints(agg)
        assert len(result) == 2
        assert c.is_feasible(agg) is False
        assert len(c.violations(agg)) == 1
