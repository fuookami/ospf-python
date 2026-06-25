"""Tests for ResourceAggregation.

资源聚合测试。
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


class TestResourceAggregationBasic:
    """ResourceAggregation 基本测试。"""

    def test_create_empty(self) -> None:
        """空聚合创建。"""
        agg = ResourceAggregation()
        assert len(agg.resources) == 0
        assert len(agg.demands) == 0

    def test_with_resource(self) -> None:
        """添加资源。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        agg = ResourceAggregation().with_resource(r)
        assert len(agg.resources) == 1
        assert agg.get_resource("res-1") == r

    def test_with_capacity(self) -> None:
        """添加容量记录。"""
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        agg = ResourceAggregation().with_capacity(cap)
        assert len(agg.capacities) == 1

    def test_with_demand(self) -> None:
        """添加需求。"""
        d = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        agg = ResourceAggregation().with_demand(d)
        assert len(agg.demands) == 1

    def test_demands_for_resource(self) -> None:
        """按资源查询需求。"""
        d1 = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        d2 = ResourceDemand(
            resource_key="res-2",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=3.0,
        )
        agg = ResourceAggregation().with_demand(d1).with_demand(d2)
        result = agg.demands_for_resource("res-1")
        assert len(result) == 1
        assert result[0].resource_key == "res-1"

    def test_demands_for_task(self) -> None:
        """按任务查询需求。"""
        d1 = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        d2 = ResourceDemand(
            resource_key="res-1",
            task_key="task-2",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=3.0,
        )
        agg = ResourceAggregation().with_demand(d1).with_demand(d2)
        result = agg.demands_for_task("task-1")
        assert len(result) == 1
        assert result[0].task_key == "task-1"

    def test_total_demand_for_resource(self) -> None:
        """计算资源总需求。"""
        d1 = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        d2 = ResourceDemand(
            resource_key="res-1",
            task_key="task-2",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=3.0,
        )
        agg = ResourceAggregation().with_demand(d1).with_demand(d2)
        assert agg.total_demand_for_resource("res-1") == 8.0

    def test_compute_utilization(self) -> None:
        """计算资源利用率。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        d = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=6.0,
        )
        agg = ResourceAggregation(
            resources=(r,),
            demands=(d,),
        )
        util = agg.compute_utilization("res-1")
        assert util.resource_key == "res-1"
        assert util.used_capacity == 6.0
        assert util.total_capacity == 10.0
        assert util.utilization_rate == 0.6

    def test_get_resource_not_found(self) -> None:
        """查找不存在的资源返回 None。"""
        agg = ResourceAggregation()
        assert agg.get_resource("nonexistent") is None

    def test_immutability(self) -> None:
        """聚合不可变。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        agg1 = ResourceAggregation()
        agg2 = agg1.with_resource(r)
        assert len(agg1.resources) == 0
        assert len(agg2.resources) == 1
