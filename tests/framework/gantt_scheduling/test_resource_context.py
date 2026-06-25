"""Tests for ResourceContext.

资源上下文测试。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
    ResourceDemand,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_shadow_price_map import (
    ResourceShadowPriceMap,
)


class TestResourceContextBasic:
    """ResourceContext 基本测试。"""

    def test_create_empty(self) -> None:
        """空上下文创建。"""
        ctx = ResourceContext()
        assert ctx is not None

    def test_register_resource(self) -> None:
        """注册资源。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        ctx = ResourceContext().register_resource(r)
        assert ctx.get_resource("res-1") == r

    def test_register_capacity(self) -> None:
        """注册容量。"""
        cap = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        ctx = ResourceContext().register_capacity(cap)
        assert len(ctx.aggregation.capacities) == 1

    def test_register_demand(self) -> None:
        """注册需求。"""
        d = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        ctx = ResourceContext().register_demand(d)
        assert len(ctx.aggregation.demands) == 1

    def test_remaining_capacity_with_resource(self) -> None:
        """有资源时计算剩余容量。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        ctx = ResourceContext().register_resource(r)
        remaining = ctx.remaining_capacity(
            resource_key="res-1",
            window_start=0.0,
            window_end=10.0,
        )
        assert remaining == 10.0

    def test_remaining_capacity_no_resource(self) -> None:
        """无资源时返回 0。"""
        ctx = ResourceContext()
        assert (
            ctx.remaining_capacity(
                resource_key="nonexistent",
                window_start=0.0,
                window_end=10.0,
            )
            == 0.0
        )

    def test_update_shadow_prices(self) -> None:
        """更新影子价格。"""
        spm = ResourceShadowPriceMap().with_resource_price(
            resource_key="res-1",
            window_start=0.0,
            window_end=10.0,
            price=2.5,
        )
        ctx = ResourceContext().update_shadow_prices(spm)
        assert (
            ctx.get_shadow_price(
                resource_key="res-1",
                window_start=0.0,
                window_end=10.0,
            )
            == 2.5
        )

    def test_compute_utilization(self) -> None:
        """计算利用率。"""
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
        ctx = ResourceContext().register_resource(r).register_demand(d)
        util = ctx.compute_utilization("res-1")
        assert util.utilization_rate == 0.6

    def test_pricing_cost_for_task(self) -> None:
        """计算任务定价成本。"""
        d = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        spm = ResourceShadowPriceMap().with_resource_price(
            resource_key="res-1",
            window_start=0.0,
            window_end=10.0,
            price=2.0,
        )
        ctx = ResourceContext().register_demand(d).update_shadow_prices(spm)
        cost = ctx.pricing_cost_for_task("task-1")
        assert cost == 10.0

    def test_get_all_resources(self) -> None:
        """获取所有资源。"""
        r1 = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        r2 = Resource(
            resource_key="res-2",
            name="M2",
            capacity=5.0,
        )
        ctx = ResourceContext().register_resource(r1).register_resource(r2)
        all_res = ctx.get_all_resources()
        assert len(all_res) == 2

    def test_immutability(self) -> None:
        """上下文不可变。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        ctx1 = ResourceContext()
        ctx2 = ctx1.register_resource(r)
        assert ctx1.get_resource("res-1") is None
        assert ctx2.get_resource("res-1") == r
