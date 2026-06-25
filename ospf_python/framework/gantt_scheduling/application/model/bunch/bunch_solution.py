"""束编组调度方案定义 / Bunch scheduling solution definition.

封装束编组的调度结果，包括任务分配和总成本。
Encapsulates the scheduling result of a bunch, including
task assignments and total cost.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchAssignment:
    """束编组任务分配 / Bunch task assignment.

    记录单个任务在束编组中的分配信息。
    Records the assignment information of a single task
    within a bunch.

    Attributes:
        task_key: 任务键 / Task key.
        start_time: 开始时间（秒）/ Start time (seconds).
    """

    task_key: str
    start_time: float


@dataclass(frozen=True)
class BunchSolution:
    """束编组调度方案 / Bunch scheduling solution.

    记录束编组的完整调度结果，包含任务分配列表和汇总指标。
    Records the complete scheduling result of a bunch,
    containing task assignment list and summary metrics.

    Attributes:
        bunch_key: 束编组键 / Bunch key.
        bunch_assignments: 任务分配元组 / Task assignment tuple.
        total_cost: 总成本 / Total cost.
        resource_key: 分配的资源键 / Assigned resource key.
    """

    bunch_key: str = ""
    bunch_assignments: tuple[BunchAssignment, ...] = ()
    total_cost: float = 0.0
    resource_key: str = ""

    # ==================== 查询 / Queries =========================

    @property
    def task_count(self) -> int:
        """获取已分配任务数量 / Get assigned task count.

        Returns:
            分配条目数量 / Number of assignment entries.
        """
        return len(self.bunch_assignments)

    @property
    def is_empty(self) -> bool:
        """是否为空方案 / Whether empty solution.

        Returns:
            无分配条目时返回 True / True when no assignments.
        """
        return len(self.bunch_assignments) == 0

    @property
    def task_keys(self) -> tuple[str, ...]:
        """获取所有已分配任务键 / Get all assigned task keys.

        Returns:
            任务键元组 / Task key tuple.
        """
        return tuple(a.task_key for a in self.bunch_assignments)

    @property
    def earliest_start(self) -> float:
        """获取最早开始时间 / Get earliest start time.

        Returns:
            所有分配中最早的开始时间，无分配时返回 0.0。
            Earliest start time among all assignments,
            0.0 when no assignments.
        """
        if not self.bunch_assignments:
            return 0.0
        return min(a.start_time for a in self.bunch_assignments)

    def assignment_for(
        self,
        task_key: str,
    ) -> BunchAssignment | None:
        """获取指定任务的分配信息 / Get assignment for task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            分配信息或 None / Assignment or None.
        """
        for assignment in self.bunch_assignments:
            if assignment.task_key == task_key:
                return assignment
        return None

    def contains_task(self, task_key: str) -> bool:
        """检查是否包含指定任务 / Check if contains a task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            包含该任务时返回 True / True when containing.
        """
        return any(a.task_key == task_key for a in self.bunch_assignments)
