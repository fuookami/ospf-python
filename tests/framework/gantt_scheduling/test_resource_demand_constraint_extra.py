"""资源需求约束额外测试 / Resource demand constraint extra tests.

补充覆盖资源域 ResourceDemandConstraint 的约束构建、
可行性检查和需求满足分析。
Supplementary coverage for resource domain
ResourceDemandConstraint constraint building, feasibility
checking, and demand satisfaction analysis.
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
    ResourceAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
    ResourceDemand,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_demand_constraint import (
    DemandSatisfaction,
    ResourceDemandConstraint,
)

# ==================== 辅助函数 / Helper functions ================


def _make_aggregation(
    *,
    resources: tuple[Resource, ...] = (),
    capacities: tuple[ResourceCapacity, ...] = (),
    demands: tuple[ResourceDemand, ...] = (),
) -> ResourceAggregation:
    """构建测试用资源聚合。/ Build test resource aggregation."""
    return ResourceAggregation(
        resources=resources,
        capacities=capacities,
        demands=demands,
    )


# ==================== DemandSatisfaction 测试 ======================


class TestDemandSatisfaction:
    """DemandSatisfaction 数据类测试。/ DemandSatisfaction tests."""

    def test_satisfied_demand(self) -> None:
        """已满足需求。/ Satisfied demand."""
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        ds = DemandSatisfaction(
            demand=demand,
            is_satisfied=True,
            shortfall=0.0,
        )
        assert ds.is_satisfied is True
        assert ds.shortfall == 0.0

    def test_unsatisfied_demand(self) -> None:
        """未满足需求。/ Unsatisfied demand."""
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=10.0,
        )
        ds = DemandSatisfaction(
            demand=demand,
            is_satisfied=False,
            shortfall=5.0,
        )
        assert ds.is_satisfied is False
        assert ds.shortfall == 5.0


# ==================== constraint_name 测试 ========================


class TestConstraintName:
    """constraint_name 方法测试。/ constraint_name tests."""

    def test_default_prefix(self) -> None:
        """默认前缀。/ Default prefix."""
        c = ResourceDemandConstraint()
        name = c.constraint_name(
            task_key="t1",
            resource_key="r1",
        )
        assert name == "resource_demand_t1_r1"

    def test_custom_prefix(self) -> None:
        """自定义前缀。/ Custom prefix."""
        c = ResourceDemandConstraint(
            constraint_name_prefix="custom",
        )
        name = c.constraint_name(
            task_key="t1",
            resource_key="r1",
        )
        assert name == "custom_t1_r1"


# ==================== build_constraints 测试 ======================


class TestBuildConstraints:
    """build_constraints 方法测试。/ build_constraints tests."""

    def test_empty_demands(self) -> None:
        """无需求返回空。/ No demands returns empty."""
        c = ResourceDemandConstraint()
        agg = _make_aggregation()
        results = c.build_constraints(agg)
        assert results == ()

    def test_demand_with_capacity_satisfied(self) -> None:
        """有容量且满足的需求。/ Demand with capacity satisfied."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=3.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        results = c.build_constraints(agg)
        assert len(results) == 1
        assert results[0].is_satisfied is True

    def test_demand_with_capacity_unsatisfied(self) -> None:
        """有容量但不满足的需求。/ Demand with capacity unsatisfied."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=8.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        results = c.build_constraints(agg)
        assert len(results) == 1
        # remaining = 10 - 8 = 2, demand = 5, shortfall = 3
        assert results[0].is_satisfied is False
        assert results[0].shortfall == 3.0

    def test_demand_no_capacity_no_resource(self) -> None:
        """无容量无资源时未满足。/ No capacity no resource unsatisfied."""
        c = ResourceDemandConstraint()
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(demands=(demand,))
        results = c.build_constraints(agg)
        assert len(results) == 1
        assert results[0].is_satisfied is False
        assert results[0].shortfall == 5.0

    def test_demand_no_capacity_with_resource(self) -> None:
        """无容量记录但有资源时用资源容量。/ No capacity record with resource."""
        c = ResourceDemandConstraint()
        resource = Resource(
            resource_key="r1",
            name="R1",
            capacity=10.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(
            resources=(resource,),
            demands=(demand,),
        )
        results = c.build_constraints(agg)
        assert len(results) == 1
        # effective capacity = 10.0 (no availability windows)
        assert results[0].is_satisfied is True

    def test_multiple_demands(self) -> None:
        """多个需求。/ Multiple demands."""
        c = ResourceDemandConstraint()
        cap1 = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=0.0,
        )
        cap2 = ResourceCapacity(
            resource_key="r2",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=5.0,
            used_capacity=4.0,
        )
        d1 = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=8.0,
        )
        d2 = ResourceDemand(
            resource_key="r2",
            task_key="t2",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=3.0,
        )
        agg = _make_aggregation(
            capacities=(cap1, cap2),
            demands=(d1, d2),
        )
        results = c.build_constraints(agg)
        assert len(results) == 2


# ==================== unsatisfied_demands 测试 ====================


class TestUnsatisfiedDemands:
    """unsatisfied_demands 方法测试。/ unsatisfied_demands tests."""

    def test_all_satisfied(self) -> None:
        """全部满足返回空。/ All satisfied returns empty."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=0.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        result = c.unsatisfied_demands(agg)
        assert result == ()

    def test_some_unsatisfied(self) -> None:
        """部分未满足。/ Some unsatisfied."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=5.0,
            used_capacity=4.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        result = c.unsatisfied_demands(agg)
        assert len(result) == 1
        assert result[0].shortfall > 0.0


# ==================== mandatory_violations 测试 ===================


class TestMandatoryViolations:
    """mandatory_violations 方法测试。/ mandatory_violations tests."""

    def test_no_mandatory_violations(self) -> None:
        """无刚性需求违反。/ No mandatory violations."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=0.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
            is_mandatory=True,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        result = c.mandatory_violations(agg)
        assert result == ()

    def test_mandatory_violation_detected(self) -> None:
        """刚性需求违反被检测。/ Mandatory violation detected."""
        c = ResourceDemandConstraint()
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=10.0,
            is_mandatory=True,
        )
        agg = _make_aggregation(demands=(demand,))
        result = c.mandatory_violations(agg)
        assert len(result) == 1

    def test_flexible_not_counted_as_violation(self) -> None:
        """柔性需求不计入违反。/ Flexible not counted as violation."""
        c = ResourceDemandConstraint()
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=10.0,
            is_mandatory=False,
        )
        agg = _make_aggregation(demands=(demand,))
        result = c.mandatory_violations(agg)
        assert result == ()


# ==================== is_feasible 测试 ============================


class TestIsFeasible:
    """is_feasible 方法测试。/ is_feasible tests."""

    def test_empty_demands_feasible(self) -> None:
        """无需求可行。/ No demands feasible."""
        c = ResourceDemandConstraint()
        agg = _make_aggregation()
        assert c.is_feasible(agg) is True

    def test_all_satisfied_feasible(self) -> None:
        """全部满足可行。/ All satisfied feasible."""
        c = ResourceDemandConstraint()
        cap = ResourceCapacity(
            resource_key="r1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=0.0,
        )
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
            is_mandatory=True,
        )
        agg = _make_aggregation(
            capacities=(cap,),
            demands=(demand,),
        )
        assert c.is_feasible(agg) is True

    def test_mandatory_unsatisfied_infeasible(self) -> None:
        """刚性需求未满足不可行。/ Mandatory unsatisfied infeasible."""
        c = ResourceDemandConstraint()
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=10.0,
            is_mandatory=True,
        )
        agg = _make_aggregation(demands=(demand,))
        assert c.is_feasible(agg) is False

    def test_flexible_unsatisfied_still_feasible(self) -> None:
        """柔性需求未满足仍可行。/ Flexible unsatisfied still feasible."""
        c = ResourceDemandConstraint()
        demand = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=10.0,
            is_mandatory=False,
        )
        agg = _make_aggregation(demands=(demand,))
        assert c.is_feasible(agg) is True
