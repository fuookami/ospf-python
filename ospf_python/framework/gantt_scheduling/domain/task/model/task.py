"""任务模型 / Task model.

定义甘特调度中任务的核心数据结构。
Defines the core task data structure in gantt scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import (
    TaskType,
)


@dataclass(frozen=True)
class Task:
    """任务数据对象 / Task data object.

    表示甘特调度中的一个可调度任务，包含时间、资源需求等信息。
    Represents a schedulable task in gantt scheduling,
    containing timing, resource requirements, etc.

    Attributes:
        task_key: 任务唯一标识 / Unique task identifier.
        name: 任务名称 / Task name.
        duration: 任务持续时长（秒）/ Task duration (seconds).
        priority: 优先级（数值越大越优先）/ Priority
            (higher = more preferred).
        earliest_start: 最早可开始时间（秒）/ Earliest start
            time (seconds).
        deadline: 截止时间（秒）/ Deadline (seconds).
        resource_requirements: 资源需求元组，每项为
            (资源键, 需求量) / Resource requirements tuple,
            each item is (resource_key, amount).
        task_type: 任务类型 / Task type.
    """

    task_key: str
    name: str
    duration: float
    priority: int = 0
    earliest_start: float = 0.0
    deadline: float = float("inf")
    resource_requirements: tuple[tuple[str, float], ...] = ()
    task_type: TaskType = TaskType.FIXED

    @staticmethod
    def create(
        *,
        task_key: str,
        name: str,
        duration: float,
        priority: int = 0,
        earliest_start: float = 0.0,
        deadline: float = float("inf"),
        resource_requirements: tuple[tuple[str, float], ...] = (),
        task_type: TaskType = TaskType.FIXED,
    ) -> Task:
        """工厂方法创建任务 / Factory method to create a task.

        Args:
            task_key: 任务唯一标识 / Unique task identifier.
            name: 任务名称 / Task name.
            duration: 持续时长（秒）/ Duration (seconds).
            priority: 优先级 / Priority.
            earliest_start: 最早开始时间 / Earliest start.
            deadline: 截止时间 / Deadline.
            resource_requirements: 资源需求 / Resource
                requirements.
            task_type: 任务类型 / Task type.

        Returns:
            新的任务实例 / New task instance.
        """
        return Task(
            task_key=task_key,
            name=name,
            duration=duration,
            priority=priority,
            earliest_start=earliest_start,
            deadline=deadline,
            resource_requirements=resource_requirements,
            task_type=task_type,
        )

    @property
    def latest_start(self) -> float:
        """最晚可开始时间 / Latest possible start time.

        Returns:
            截止时间减去持续时长。
            Deadline minus duration.
        """
        if self.deadline == float("inf"):
            return float("inf")
        return max(0.0, self.deadline - self.duration)

    @property
    def earliest_end(self) -> float:
        """最早结束时间 / Earliest end time.

        Returns:
            最早开始时间加上持续时长。
            Earliest start plus duration.
        """
        return self.earliest_start + self.duration

    @property
    def time_window(self) -> float:
        """可用时间窗口大小 / Available time window size.

        Returns:
            截止时间减去最早开始时间。
            Deadline minus earliest start.
        """
        if self.deadline == float("inf"):
            return float("inf")
        return max(0.0, self.deadline - self.earliest_start)

    @property
    def slack(self) -> float:
        """松弛时间 / Slack time.

        最晚开始时间与最早开始时间的差值。
        Difference between latest and earliest start times.

        Returns:
            松弛时间（秒）/ Slack time (seconds).
        """
        return max(0.0, self.latest_start - self.earliest_start)

    @property
    def resource_keys(self) -> tuple[str, ...]:
        """获取所需资源键列表 / Get required resource keys.

        Returns:
            去重的资源键元组 / Deduplicated resource key tuple.
        """
        return tuple(dict.fromkeys(k for k, _ in self.resource_requirements))

    def resource_demand(self, resource_key: str) -> float:
        """获取指定资源的需求量 / Get demand for a specific resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            该资源的总需求量，不存在时返回 0.0。
            Total demand for the resource, 0.0 if absent.
        """
        return sum(
            amount for key, amount in self.resource_requirements if key == resource_key
        )

    def requires_resource(self, resource_key: str) -> bool:
        """检查是否需要指定资源 / Check if requires a resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            是否需要该资源 / Whether the resource is needed.
        """
        return any(key == resource_key for key, _ in self.resource_requirements)

    def is_feasible_in_window(
        self,
        window_start: float,
        window_end: float,
    ) -> bool:
        """检查任务在给定时间窗口内是否可行。

        Check if the task is feasible within a time window.

        Args:
            window_start: 窗口起始时间 / Window start.
            window_end: 窗口结束时间 / Window end.

        Returns:
            是否可行 / Whether feasible.
        """
        available_start = max(self.earliest_start, window_start)
        available_end = min(self.deadline, window_end)
        return available_end - available_start >= self.duration

    def with_deadline(self, deadline: float) -> Task:
        """创建不同截止时间的任务 / Create task with different deadline.

        Args:
            deadline: 新截止时间 / New deadline.

        Returns:
            新任务实例 / New task instance.
        """
        return Task(
            task_key=self.task_key,
            name=self.name,
            duration=self.duration,
            priority=self.priority,
            earliest_start=self.earliest_start,
            deadline=deadline,
            resource_requirements=self.resource_requirements,
            task_type=self.task_type,
        )

    def __str__(self) -> str:
        """字符串表示 / String representation."""
        return f"Task({self.task_key}: {self.name})"
