"""资源上下文 / Resource context.

资源域的建模入口，负责初始化聚合并注册到优化模型。
The modeling entry point for the resource domain, responsible
for initializing aggregation and registering to the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
    ResourceAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_shadow_price_map import (
    ResourceShadowPriceMap,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
        Resource,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
        ResourceCapacity,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
        ResourceDemand,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
        ResourceUtilization,
    )


@dataclass(frozen=True)
class ResourceContext:
    """资源上下文 / Resource context.

    作为资源域对应用层暴露的建模入口，管理资源注册表和聚合状态。
    提供资源的注册、查询、容量计算和影子价格管理。
    Serves as the modeling entry point exposed to the application
    layer, managing the resource registry and aggregation state.
    Provides resource registration, querying, capacity computation,
    and shadow price management.

    Attributes:
        aggregation: 资源聚合 / Resource aggregation.
        shadow_price_map: 影子价格映射 / Shadow price map.
    """

    aggregation: ResourceAggregation = field(
        default_factory=ResourceAggregation,
    )
    shadow_price_map: ResourceShadowPriceMap = field(
        default_factory=ResourceShadowPriceMap,
    )

    # ==================== 资源注册 / Resource registration ========

    def register_resource(self, resource: Resource) -> ResourceContext:
        """注册新资源。

        Register a new resource.

        Args:
            resource: 待注册的资源。/ Resource to register.

        Returns:
            包含新资源的 ResourceContext 副本。
            A new ResourceContext with the resource registered.
        """
        return ResourceContext(
            aggregation=self.aggregation.with_resource(resource),
            shadow_price_map=self.shadow_price_map,
        )

    def register_capacity(
        self,
        capacity: ResourceCapacity,
    ) -> ResourceContext:
        """注册资源容量记录。

        Register a resource capacity record.

        Args:
            capacity: 容量记录。/ Capacity record.

        Returns:
            包含新容量记录的 ResourceContext 副本。
            A new ResourceContext with the capacity registered.
        """
        return ResourceContext(
            aggregation=self.aggregation.with_capacity(capacity),
            shadow_price_map=self.shadow_price_map,
        )

    def register_demand(
        self,
        demand: ResourceDemand,
    ) -> ResourceContext:
        """注册资源需求。

        Register a resource demand.

        Args:
            demand: 资源需求。/ Resource demand.

        Returns:
            包含新需求的 ResourceContext 副本。
            A new ResourceContext with the demand registered.
        """
        return ResourceContext(
            aggregation=self.aggregation.with_demand(demand),
            shadow_price_map=self.shadow_price_map,
        )

    # ==================== 查询 / Queries =========================

    def get_resource(self, resource_key: str) -> Resource | None:
        """按标识查找资源。

        Find a resource by its key.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            匹配的资源，不存在时返回 None。
            Matching resource, or None if not found.
        """
        return self.aggregation.get_resource(resource_key)

    def get_all_resources(self) -> tuple[Resource, ...]:
        """获取所有已注册资源。

        Get all registered resources.

        Returns:
            资源元组。/ Tuple of resources.
        """
        return self.aggregation.resources

    def demands_for_task(
        self,
        task_key: str,
    ) -> tuple[ResourceDemand, ...]:
        """获取指定任务的所有资源需求。

        Get all resource demands for a specific task.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            需求元组。/ Tuple of demands.
        """
        return self.aggregation.demands_for_task(task_key)

    # ==================== 容量计算 / Capacity computation ========

    def remaining_capacity(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> float:
        """计算指定资源在时间窗口内的剩余容量。

        Compute remaining capacity of a resource within a
        time window.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            剩余容量，资源不存在时返回 0.0。
            Remaining capacity, or 0.0 if resource not found.
        """
        cap = self.aggregation.get_capacity(
            resource_key=resource_key,
            window_start=window_start,
            window_end=window_end,
        )
        if cap is None:
            resource = self.aggregation.get_resource(resource_key)
            if resource is None:
                return 0.0
            return resource.effective_capacity_during(
                start=window_start,
                end=window_end,
            )
        return cap.remaining_capacity

    # ==================== 影子价格 / Shadow prices ===============

    def update_shadow_prices(
        self,
        shadow_price_map: ResourceShadowPriceMap,
    ) -> ResourceContext:
        """更新影子价格映射。

        Update the shadow price map.

        Args:
            shadow_price_map: 新的影子价格映射 /
                New shadow price map.

        Returns:
            影子价格更新后的 ResourceContext 副本。
            A new ResourceContext with updated shadow prices.
        """
        return ResourceContext(
            aggregation=self.aggregation,
            shadow_price_map=shadow_price_map,
        )

    def get_shadow_price(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> float:
        """获取资源约束的影子价格。

        Get the shadow price for a resource constraint.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            影子价格，不存在时返回 0.0。
            Shadow price, or 0.0 if not found.
        """
        return self.shadow_price_map.get_resource_price(
            resource_key=resource_key,
            window_start=window_start,
            window_end=window_end,
        )

    # ==================== 利用率 / Utilization ====================

    def compute_utilization(
        self,
        resource_key: str,
    ) -> ResourceUtilization:
        """计算指定资源的利用率。

        Compute utilization for a specific resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            资源利用率指标。/ Resource utilization metrics.
        """
        return self.aggregation.compute_utilization(resource_key)

    def compute_all_utilizations(self) -> tuple[ResourceUtilization, ...]:
        """计算所有资源的利用率。

        Compute utilization for all registered resources.

        Returns:
            利用率指标元组。/ Tuple of utilization metrics.
        """
        return tuple(
            self.compute_utilization(r.resource_key) for r in self.aggregation.resources
        )

    # ==================== 定价成本 / Pricing cost ================

    def pricing_cost_for_task(self, task_key: str) -> float:
        """计算指定任务的资源定价成本。

        Compute resource pricing cost for a specific task.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            定价成本。/ Pricing cost.
        """
        task_demands = self.aggregation.demands_for_task(task_key)
        demand_tuples = tuple(
            (d.resource_key, d.time_window_start, d.time_window_end, d.demand_amount)
            for d in task_demands
        )
        return self.shadow_price_map.total_pricing_cost(demand_tuples)
