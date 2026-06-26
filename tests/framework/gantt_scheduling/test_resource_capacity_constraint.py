"""资源容量约束测试。

Resource capacity constraint tests.

测试 ResourceCapacityConstraint 的构造、约束名称、
约束构建、可行性和违规检测。
Tests ResourceCapacityConstraint construction, constraint
name, constraint building, feasibility, and violations.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
    ResourceAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
    ResourceDemand,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_capacity_constraint import (
    ResourceCapacityConstraint,
)

# ── helpers ────────────────────────────────────────────────────


def _make_aggregation(
    capacities: list[ResourceCapacity],
    demands: list[ResourceDemand],
) -> ResourceAggregation:
    """构建测试用资源聚合。/ Build test resource aggregation."""
    agg = ResourceAggregation()
    for c in capacities:
        agg = agg.with_capacity(c)
    for d in demands:
        agg = agg.with_demand(d)
    return agg


# ── construction tests ─────────────────────────────────────────


class TestResourceCapacityConstraintConstruction:
    """构造测试。/ Construction tests."""

    def test_default_construction(self) -> None:
        """默认构造。/ Default construction."""
        c = ResourceCapacityConstraint()
        assert c.constraint_name_prefix == "resource_capacity"

    def test_custom_prefix(self) -> None:
        """自定义前缀。/ Custom prefix."""
        c = ResourceCapacityConstraint(
            constraint_name_prefix="rc",
        )
        assert c.constraint_name_prefix == "rc"

    def test_frozen(self) -> None:
        """不可变性。/ Frozen behavior."""
        c = ResourceCapacityConstraint()
        with pytest.raises(AttributeError):
            c.constraint_name_prefix = "x"  # type: ignore[misc]


# ── constraint_name tests ──────────────────────────────────────


class TestResourceCapacityConstraintName:
    """约束名称测试。/ Constraint name tests."""

    def test_constraint_name(self) -> None:
        """生成约束名称。/ Generate constraint name."""
        c = ResourceCapacityConstraint()
        name = c.constraint_name(
            resource_key="res-1",
            window_start=0.0,
            window_end=10.0,
        )
        assert name == "resource_capacity_res-1_0.0_10.0"

    def test_constraint_name_custom_prefix(self) -> None:
        """自定义前缀约束名。/ Custom prefix name."""
        c = ResourceCapacityConstraint(
            constraint_name_prefix="rc",
        )
        name = c.constraint_name(
            resource_key="r2",
            window_start=5.0,
            window_end=15.0,
        )
        assert name == "rc_r2_5.0_15.0"


# ── build_constraints tests ────────────────────────────────────


class TestResourceCapacityConstraintBuild:
    """构建约束测试。/ Build constraints tests."""

    def test_build_empty(self) -> None:
        """空聚合返回空约束。/ Empty aggregation returns empty."""
        c = ResourceCapacityConstraint()
        agg = ResourceAggregation()
        result = c.build_constraints(agg)
        assert result == ()

    def test_build_single_no_demand(self) -> None:
        """无需求时 used 为 0。/ No demand means used is 0."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        agg = _make_aggregation([cap], [])
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].used_capacity == 0.0

    def test_build_with_overlapping_demand(self) -> None:
        """重叠需求计入使用量。

        Overlapping demands count as used capacity.
        """
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        d1 = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=2.0,
            time_window_end=8.0,
            demand_amount=30.0,
        )
        d2 = ResourceDemand(
            resource_key="res-1",
            task_key="t2",
            time_window_start=5.0,
            time_window_end=12.0,
            demand_amount=20.0,
        )
        agg = _make_aggregation([cap], [d1, d2])
        result = c.build_constraints(agg)
        assert len(result) == 1
        assert result[0].used_capacity == 50.0

    def test_build_non_overlapping_demand_excluded(self) -> None:
        """非重叠需求不计入。/ Non-overlapping demand excluded."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=5.0,
            max_capacity=100.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=6.0,
            time_window_end=10.0,
            demand_amount=30.0,
        )
        agg = _make_aggregation([cap], [d])
        result = c.build_constraints(agg)
        assert result[0].used_capacity == 0.0

    def test_build_different_resource_excluded(self) -> None:
        """不同资源的需求不计入。/ Different resource excluded."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        d = ResourceDemand(
            resource_key="res-2",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=30.0,
        )
        agg = _make_aggregation([cap], [d])
        result = c.build_constraints(agg)
        assert result[0].used_capacity == 0.0


# ── is_feasible / violations tests ─────────────────────────────


class TestResourceCapacityConstraintFeasibility:
    """可行性测试。/ Feasibility tests."""

    def test_feasible(self) -> None:
        """可行聚合。/ Feasible aggregation."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=50.0,
        )
        agg = _make_aggregation([cap], [d])
        assert c.is_feasible(agg) is True

    def test_infeasible(self) -> None:
        """不可行聚合。/ Infeasible aggregation."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=50.0,
        )
        agg = _make_aggregation([cap], [d])
        assert c.is_feasible(agg) is False

    def test_violations_empty_when_feasible(self) -> None:
        """可行时无违反。/ No violations when feasible."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=100.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=50.0,
        )
        agg = _make_aggregation([cap], [d])
        assert c.violations(agg) == ()

    def test_violations_nonempty(self) -> None:
        """不可行时有违反。/ Has violations when infeasible."""
        c = ResourceCapacityConstraint()
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=50.0,
        )
        agg = _make_aggregation([cap], [d])
        violations = c.violations(agg)
        assert len(violations) == 1
        used = violations[0].used_capacity
        maximum = violations[0].max_capacity
        assert used > maximum

    def test_multiple_resources(self) -> None:
        """多资源约束。/ Multiple resource constraints."""
        c = ResourceCapacityConstraint()
        caps = [
            ResourceCapacity(
                resource_key="r1",
                time_window_start=0.0,
                time_window_end=10.0,
                max_capacity=100.0,
            ),
            ResourceCapacity(
                resource_key="r2",
                time_window_start=0.0,
                time_window_end=10.0,
                max_capacity=20.0,
            ),
        ]
        demands = [
            ResourceDemand(
                resource_key="r1",
                task_key="t1",
                time_window_start=0.0,
                time_window_end=10.0,
                demand_amount=30.0,
            ),
            ResourceDemand(
                resource_key="r2",
                task_key="t2",
                time_window_start=0.0,
                time_window_end=10.0,
                demand_amount=60.0,
            ),
        ]
        agg = _make_aggregation(caps, demands)
        result = c.build_constraints(agg)
        assert len(result) == 2
        assert c.is_feasible(agg) is False
        assert len(c.violations(agg)) == 1
