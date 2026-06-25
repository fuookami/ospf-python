"""资源聚合 / Resource aggregation.

组合资源域内的多个模型组件，协调容量、需求和利用率的注册。
Combines multiple model components within the resource domain,
coordinating the registration of capacities, demands, and
utilization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
        Resource,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_attribute import (
        ResourceAttribute,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_availability import (
        ResourceAvailability,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
        ResourceCapacity,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
        ResourceDemand,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand_contribution import (
        ResourceDemandContribution,
    )


@dataclass(frozen=True)
class ResourceAggregation:
    """资源聚合 / Resource aggregation.

    聚合资源域的所有模型组件，提供统一的查询和操作入口。
    负责协调资源注册、容量管理、需求分配和利用率统计。
    Aggregates all model components in the resource domain,
    providing a unified query and operation interface.
    Responsible for coordinating resource registration, capacity
    management, demand allocation, and utilization statistics.

    Attributes:
        resources: 资源映射 (key -> Resource) /
            Resource mapping (key -> Resource).
        capacities: 资源容量列表 / Resource capacity list.
        demands: 资源需求列表 / Resource demand list.
        contributions: 需求贡献列表 / Demand contribution list.
        attributes: 资源属性列表 / Resource attribute list.
        availabilities: 资源可用性列表 / Resource availability list.
    """

    resources: tuple[Resource, ...] = ()
    capacities: tuple[ResourceCapacity, ...] = ()
    demands: tuple[ResourceDemand, ...] = ()
    contributions: tuple[ResourceDemandContribution, ...] = ()
    attributes: tuple[ResourceAttribute, ...] = ()
    availabilities: tuple[ResourceAvailability, ...] = ()

    def get_resource(self, resource_key: str) -> Resource | None:
        """按标识查找资源。

        Find a resource by its key.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            匹配的资源，不存在时返回 None。
            Matching resource, or None if not found.
        """
        for r in self.resources:
            if r.resource_key == resource_key:
                return r
        return None

    def get_capacity(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> ResourceCapacity | None:
        """按资源和时间窗口查找容量记录。

        Find a capacity record by resource key and time window.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            匹配的容量记录，不存在时返回 None。
            Matching capacity record, or None if not found.
        """
        for c in self.capacities:
            if (
                c.resource_key == resource_key
                and c.time_window_start == window_start
                and c.time_window_end == window_end
            ):
                return c
        return None

    def demands_for_resource(
        self,
        resource_key: str,
    ) -> tuple[ResourceDemand, ...]:
        """获取指定资源的所有需求。

        Get all demands for a specific resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            该资源的需求元组。/ Demands tuple for the resource.
        """
        return tuple(d for d in self.demands if d.resource_key == resource_key)

    def demands_for_task(
        self,
        task_key: str,
    ) -> tuple[ResourceDemand, ...]:
        """获取指定任务的所有需求。

        Get all demands for a specific task.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            该任务的需求元组。/ Demands tuple for the task.
        """
        return tuple(d for d in self.demands if d.task_key == task_key)

    def contributions_for_task(
        self,
        task_key: str,
    ) -> tuple[ResourceDemandContribution, ...]:
        """获取指定任务的所有需求贡献。

        Get all demand contributions for a specific task.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            该任务的贡献元组。/ Contributions tuple for the task.
        """
        return tuple(c for c in self.contributions if c.task_key == task_key)

    def get_attribute(
        self,
        resource_key: str,
    ) -> ResourceAttribute | None:
        """获取指定资源的属性。

        Get attributes for a specific resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            匹配的属性集合，不存在时返回 None。
            Matching attribute collection, or None if not found.
        """
        for a in self.attributes:
            if a.resource_key == resource_key:
                return a
        return None

    def get_availability(
        self,
        resource_key: str,
    ) -> ResourceAvailability | None:
        """获取指定资源的可用性信息。

        Get availability info for a specific resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            匹配的可用性信息，不存在时返回 None。
            Matching availability info, or None if not found.
        """
        for a in self.availabilities:
            if a.resource_key == resource_key:
                return a
        return None

    def with_resource(self, resource: Resource) -> ResourceAggregation:
        """创建添加资源后的副本。

        Create a copy with an additional resource.

        Args:
            resource: 待添加的资源。/ Resource to add.

        Returns:
            包含新资源的 ResourceAggregation 副本。
            A new ResourceAggregation with the resource added.
        """
        return ResourceAggregation(
            resources=self.resources + (resource,),
            capacities=self.capacities,
            demands=self.demands,
            contributions=self.contributions,
            attributes=self.attributes,
            availabilities=self.availabilities,
        )

    def with_capacity(
        self,
        capacity: ResourceCapacity,
    ) -> ResourceAggregation:
        """创建添加容量记录后的副本。

        Create a copy with an additional capacity record.

        Args:
            capacity: 待添加的容量记录。/ Capacity record to add.

        Returns:
            包含新容量记录的 ResourceAggregation 副本。
            A new ResourceAggregation with the capacity added.
        """
        return ResourceAggregation(
            resources=self.resources,
            capacities=self.capacities + (capacity,),
            demands=self.demands,
            contributions=self.contributions,
            attributes=self.attributes,
            availabilities=self.availabilities,
        )

    def with_demand(
        self,
        demand: ResourceDemand,
    ) -> ResourceAggregation:
        """创建添加需求后的副本。

        Create a copy with an additional demand.

        Args:
            demand: 待添加的需求。/ Demand to add.

        Returns:
            包含新需求的 ResourceAggregation 副本。
            A new ResourceAggregation with the demand added.
        """
        return ResourceAggregation(
            resources=self.resources,
            capacities=self.capacities,
            demands=self.demands + (demand,),
            contributions=self.contributions,
            attributes=self.attributes,
            availabilities=self.availabilities,
        )

    def total_demand_for_resource(
        self,
        resource_key: str,
    ) -> float:
        """计算指定资源的总需求量。

        Compute total demand amount for a specific resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            总需求量。/ Total demand amount.
        """
        return sum(
            d.demand_amount for d in self.demands if d.resource_key == resource_key
        )

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
        resource = self.get_resource(resource_key)
        if resource is None:
            return ResourceUtilization(
                resource_key=resource_key,
                time_range_start=0.0,
                time_range_end=0.0,
                total_capacity=0.0,
                used_capacity=0.0,
            )

        resource_demands = self.demands_for_resource(resource_key)
        used = sum(d.demand_amount for d in resource_demands)
        peak = max(
            (d.demand_amount for d in resource_demands),
            default=0.0,
        )

        if resource_demands:
            range_start = min(d.time_window_start for d in resource_demands)
            range_end = max(d.time_window_end for d in resource_demands)
        else:
            range_start = 0.0
            range_end = 0.0

        return ResourceUtilization(
            resource_key=resource_key,
            time_range_start=range_start,
            time_range_end=range_end,
            total_capacity=resource.capacity,
            used_capacity=used,
            peak_usage=peak,
        )
