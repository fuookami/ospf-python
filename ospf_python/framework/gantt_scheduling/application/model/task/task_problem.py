"""任务调度问题定义 / Task scheduling problem definition.

封装单个任务的调度输入数据，包括时长、优先级和资源需求。
Encapsulates scheduling input data for a single task,
including duration, priority, and resource requirements.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskProblem:
    """任务调度问题 / Task scheduling problem.

    描述一个待调度任务的完整参数，用于列生成定价子问题。
    Describes the complete parameters of a task to be scheduled,
    used in column generation pricing subproblems.

    Attributes:
        task_key: 任务唯一标识 / Unique task identifier.
        duration: 任务持续时长（秒）/ Task duration (seconds).
        priority: 优先级（数值越大越优先）/ Priority
            (higher value means more preferred).
        resource_requirements: 资源需求元组，每项为
            (资源键, 需求量) / Resource requirements tuple,
            each item is (resource_key, amount).
        earliest_start: 最早可开始时间（秒）/ Earliest start
            time (seconds).
        deadline: 截止时间（秒）/ Deadline (seconds).
    """

    task_key: str = ""
    duration: float = 0.0
    priority: int = 0
    resource_requirements: tuple[tuple[str, float], ...] = ()
    earliest_start: float = 0.0
    deadline: float = float("inf")

    # ==================== 查询 / Queries =========================

    @property
    def latest_start(self) -> float:
        """最晚可开始时间 / Latest possible start time.

        Returns:
            截止时间减去持续时长；无截止时间时返回正无穷。
            Deadline minus duration; positive infinity when
            no deadline.
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
    def resource_keys(self) -> tuple[str, ...]:
        """获取所需资源键列表 / Get required resource keys.

        Returns:
            去重的资源键元组 / Deduplicated resource key tuple.
        """
        return tuple(dict.fromkeys(k for k, _ in self.resource_requirements))

    @property
    def task_count(self) -> int:
        """获取资源需求数量 / Get resource requirement count.

        Returns:
            资源需求条目数 / Number of resource requirement entries.
        """
        return len(self.resource_requirements)

    def requires_resource(self, resource_key: str) -> bool:
        """检查是否需要指定资源 / Check if requires a resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            是否需要该资源 / Whether the resource is needed.
        """
        return any(key == resource_key for key, _ in self.resource_requirements)

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
