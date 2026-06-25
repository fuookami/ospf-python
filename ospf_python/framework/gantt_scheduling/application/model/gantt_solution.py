"""甘特调度解决方案 / Gantt scheduling solution.

封装列生成求解后的调度结果和性能指标。
Encapsulates the scheduling result and performance metrics
after column generation solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
        ResourceUtilization,
    )


@dataclass(frozen=True)
class TaskScheduleEntry:
    """任务调度条目 / Task schedule entry.

    记录单个任务的调度结果。
    Records the scheduling result of a single task.

    Attributes:
        task_key: 任务键 / Task key.
        start_time: 开始时间（秒）/ Start time (seconds).
        end_time: 结束时间（秒）/ End time (seconds).
        assigned_resource: 分配的资源键 / Assigned resource key.
    """

    task_key: str
    start_time: float
    end_time: float
    assigned_resource: str = ""


@dataclass(frozen=True)
class GanttSolution:
    """甘特调度解决方案 / Gantt scheduling solution.

    包含完整的调度方案和汇总 KPI。
    Contains the complete schedule and summary KPIs.

    Attributes:
        name: 方案名称 / Solution name.
        schedule: 任务调度条目映射 (task_key -> entry) /
            Task schedule entry mapping.
        makespan: 总完工时间（秒）/ Total makespan (seconds).
        objective_value: 目标函数值 / Objective function value.
        resource_utilizations: 资源利用率列表 /
            Resource utilization list.
        is_optimal: 是否为最优解 / Whether optimal.
        solve_time: 求解耗时（秒）/ Solve time (seconds).
        gap: 最优间隙 / Optimality gap.
        iteration_count: 列生成迭代次数 /
            Column generation iteration count.
    """

    name: str = "gantt solution"
    schedule: tuple[TaskScheduleEntry, ...] = ()
    makespan: float = 0.0
    objective_value: float = 0.0
    resource_utilizations: tuple[ResourceUtilization, ...] = ()
    is_optimal: bool = False
    solve_time: float = 0.0
    gap: float = 0.0
    iteration_count: int = 0

    # ==================== 查询 / Queries =========================

    @property
    def task_count(self) -> int:
        """获取已调度任务数 / Get scheduled task count.

        Returns:
            调度条目数量 / Number of schedule entries.
        """
        return len(self.schedule)

    @property
    def has_schedule(self) -> bool:
        """是否有调度方案 / Whether has schedule.

        Returns:
            有调度条目时返回 True / True when schedule exists.
        """
        return len(self.schedule) > 0

    @property
    def resource_count(self) -> int:
        """获取涉及的资源数量 / Get involved resource count.

        Returns:
            去重后的资源数量 / Deduplicated resource count.
        """
        return len(
            set(e.assigned_resource for e in self.schedule if e.assigned_resource)
        )

    def entry_for(
        self,
        task_key: str,
    ) -> TaskScheduleEntry | None:
        """获取指定任务的调度条目 / Get schedule entry for task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            调度条目或 None / Schedule entry or None.
        """
        for entry in self.schedule:
            if entry.task_key == task_key:
                return entry
        return None

    def entries_for_resource(
        self,
        resource_key: str,
    ) -> tuple[TaskScheduleEntry, ...]:
        """获取指定资源的所有调度条目。

        Get all schedule entries for a specific resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            该资源的调度条目元组。
            Schedule entry tuple for the resource.
        """
        return tuple(e for e in self.schedule if e.assigned_resource == resource_key)

    @property
    def average_utilization(self) -> float:
        """获取平均资源利用率 / Get average resource utilization.

        Returns:
            所有资源利用率的平均值，无资源时返回 0.0。
            Average utilization across all resources, 0.0
            when no resources.
        """
        if not self.resource_utilizations:
            return 0.0
        return sum(u.utilization_rate for u in self.resource_utilizations) / len(
            self.resource_utilizations
        )

    @property
    def peak_utilization(self) -> float:
        """获取峰值资源利用率 / Get peak resource utilization.

        Returns:
            所有资源中的最高利用率，无资源时返回 0.0。
            Highest utilization among all resources, 0.0
            when no resources.
        """
        if not self.resource_utilizations:
            return 0.0
        return max(u.utilization_rate for u in self.resource_utilizations)

    @property
    def idle_resources(self) -> tuple[str, ...]:
        """获取空闲资源键 / Get idle resource keys.

        Returns:
            利用率为零的资源键元组。
            Resource key tuple with zero utilization.
        """
        return tuple(
            u.resource_key for u in self.resource_utilizations if u.used_capacity <= 0.0
        )

    def utilization_for(
        self,
        resource_key: str,
    ) -> ResourceUtilization | None:
        """获取指定资源的利用率 / Get utilization for resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            资源利用率或 None / Resource utilization or None.
        """
        for u in self.resource_utilizations:
            if u.resource_key == resource_key:
                return u
        return None
