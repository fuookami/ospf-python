"""任务上下文 / Task context.

管理任务注册表和任务生命周期。
Manages the task registry and task lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.task.error.gantt_errors import (
    GanttErrors,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
        Task,
    )


class TaskContext:
    """任务上下文 / Task context.

    维护任务注册表，提供任务的注册、查询和管理功能。
    在甘特调度中充当任务的中央仓库。
    Maintains the task registry, providing registration,
    query, and management functions. Acts as the central
    repository for tasks in gantt scheduling.

    Attributes:
        _tasks: 内部任务字典 / Internal task dictionary.
    """

    def __init__(self) -> None:
        """初始化空任务上下文 / Initialize empty task context."""
        self._tasks: dict[str, Task] = {}

    def register(self, task: Task) -> Result[None, str, Err[str]]:
        """注册任务 / Register a task.

        如果任务键已存在，返回失败结果。
        Returns a failure result if the task key already exists.

        Args:
            task: 要注册的任务 / Task to register.

        Returns:
            注册结果 / Registration result.
        """
        if task.task_key in self._tasks:
            return Failed(
                Err(
                    _code=GanttErrors.DUPLICATE_TASK.value,  # type: ignore[arg-type]
                    _message=(
                        f"任务键已存在: {task.task_key} / "
                        f"Task key already exists: {task.task_key}"
                    ),
                )
            )
        self._tasks[task.task_key] = task
        return Ok(None)

    def unregister(
        self,
        task_key: str,
    ) -> Result[None, str, Err[str]]:
        """注销任务 / Unregister a task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            注销结果 / Unregistration result.
        """
        if task_key not in self._tasks:
            return Failed(
                Err(
                    _code=GanttErrors.TASK_NOT_FOUND.value,  # type: ignore[arg-type]
                    _message=(f"任务未找到: {task_key} / Task not found: {task_key}"),
                )
            )
        del self._tasks[task_key]
        return Ok(None)

    def get(self, key: str) -> Task | None:
        """获取任务 / Get a task.

        Args:
            key: 任务键 / Task key.

        Returns:
            任务实例或 None / Task instance or None.
        """
        return self._tasks.get(key)

    def get_or_error(
        self,
        key: str,
    ) -> Result[Task, str, Err[str]]:
        """获取任务或返回错误 / Get task or return error.

        Args:
            key: 任务键 / Task key.

        Returns:
            包含任务的成功结果或失败结果。
            Success result with task or failure result.
        """
        task = self._tasks.get(key)
        if task is None:
            return Failed(
                Err(
                    _code=GanttErrors.TASK_NOT_FOUND.value,  # type: ignore[arg-type]
                    _message=(f"任务未找到: {key} / Task not found: {key}"),
                )
            )
        return Ok(task)

    def tasks(self) -> tuple[Task, ...]:
        """获取所有已注册任务 / Get all registered tasks.

        Returns:
            任务元组 / Task tuple.
        """
        return tuple(self._tasks.values())

    def task_keys(self) -> tuple[str, ...]:
        """获取所有任务键 / Get all task keys.

        Returns:
            任务键元组 / Task key tuple.
        """
        return tuple(self._tasks.keys())

    def contains(self, key: str) -> bool:
        """检查任务是否存在 / Check if task exists.

        Args:
            key: 任务键 / Task key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._tasks

    @property
    def size(self) -> int:
        """获取任务数量 / Get task count.

        Returns:
            已注册任务数量 / Number of registered tasks.
        """
        return len(self._tasks)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册任务时返回 True。
            True when no tasks registered.
        """
        return len(self._tasks) == 0

    def filter_by_priority(
        self,
        min_priority: int,
    ) -> tuple[Task, ...]:
        """按优先级过滤任务 / Filter tasks by priority.

        Args:
            min_priority: 最低优先级 / Minimum priority.

        Returns:
            满足优先级要求的任务元组。
            Task tuple meeting priority requirement.
        """
        return tuple(t for t in self._tasks.values() if t.priority >= min_priority)

    def filter_by_resource(
        self,
        resource_key: str,
    ) -> tuple[Task, ...]:
        """按资源需求过滤任务 / Filter tasks by resource demand.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            需要该资源的任务元组。
            Task tuple requiring the resource.
        """
        return tuple(
            t for t in self._tasks.values() if t.requires_resource(resource_key)
        )

    def clear(self) -> None:
        """清空所有任务 / Clear all tasks."""
        self._tasks.clear()
