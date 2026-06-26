"""Task context for registration and lookup.

任务注册与查找上下文。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .task_aggregation import TaskAggregation

if TYPE_CHECKING:
    from .flight_task import FlightTask
    from .task_priority import TaskPriority
    from .task_requirement import TaskRequirement
    from .task_result import TaskResult
    from .task_status import TaskStatus


class TaskContext:
    """Mutable registry for flight tasks with lookup capabilities.

    支持查找功能的航班任务可变注册表。
    """

    def __init__(self) -> None:
        """Initialize empty task context.

        初始化空的任务上下文。
        """
        self._tasks: dict[str, FlightTask] = {}
        self._requirements: dict[str, TaskRequirement] = {}
        self._results: dict[str, TaskResult] = {}

    def register_task(self, task: FlightTask) -> None:
        """Register a flight task.

        注册航班任务。

        Args:
            task: Flight task to register.
        """
        self._tasks[task.task_id] = task

    def register_requirement(
        self,
        requirement: TaskRequirement,
    ) -> None:
        """Register a task requirement.

        注册任务需求。

        Args:
            requirement: Task requirement to register.
        """
        self._requirements[requirement.task_id] = requirement

    def register_result(
        self,
        result: TaskResult,
    ) -> None:
        """Register a task result.

        注册任务结果。

        Args:
            result: Task result to register.
        """
        self._results[result.task_id] = result

    def get_task(
        self,
        task_id: str,
    ) -> FlightTask | None:
        """Look up a task by ID.

        按 ID 查找任务。

        Args:
            task_id: Unique task identifier.

        Returns:
            The flight task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def get_requirement(
        self,
        task_id: str,
    ) -> TaskRequirement | None:
        """Look up a task requirement by task ID.

        按任务 ID 查找任务需求。

        Args:
            task_id: Unique task identifier.

        Returns:
            The requirement if found, None otherwise.
        """
        return self._requirements.get(task_id)

    def get_result(
        self,
        task_id: str,
    ) -> TaskResult | None:
        """Look up a task result by task ID.

        按任务 ID 查找任务结果。

        Args:
            task_id: Unique task identifier.

        Returns:
            The result if found, None otherwise.
        """
        return self._results.get(task_id)

    def get_tasks_by_status(
        self,
        status: TaskStatus,
    ) -> Sequence[FlightTask]:
        """Get all tasks with a given status.

        获取具有给定状态的所有任务。

        Args:
            status: Status to filter by.

        Returns:
            Sequence of matching flight tasks.
        """
        return tuple(t for t in self._tasks.values() if t.status == status)

    def get_tasks_by_priority(
        self,
        priority: TaskPriority,
    ) -> Sequence[FlightTask]:
        """Get all tasks with a given priority.

        获取具有给定优先级的所有任务。

        Args:
            priority: Priority to filter by.

        Returns:
            Sequence of matching flight tasks.
        """
        return tuple(t for t in self._tasks.values() if t.priority == priority)

    def build_aggregation(self) -> TaskAggregation:
        """Build an aggregation of all registered tasks.

        构建所有已注册任务的聚合。

        Returns:
            TaskAggregation grouped by status and priority.
        """
        return TaskAggregation.from_tasks(list(self._tasks.values()))

    @property
    def task_count(self) -> int:
        """Number of registered tasks.

        已注册任务的数量。
        """
        return len(self._tasks)
