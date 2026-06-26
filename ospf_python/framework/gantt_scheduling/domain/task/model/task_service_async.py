"""任务异步服务抽象基类 / Task async service ABC.

定义任务域的异步服务接口。
Defines async service interfaces for the task domain.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
        Task,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_aggregation import (
        TaskAggregation,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
        TaskContext,
    )
    from ospf_python.utils.error.error import Err
    from ospf_python.utils.functional.result import Result


class TaskServiceAsync(abc.ABC):
    """任务异步服务抽象基类 / Task async service abstract base class.

    定义任务调度服务的核心异步操作接口。
    子类需实现具体的调度算法和业务逻辑。
    Defines the core async operation interface for task
    scheduling services. Subclasses must implement concrete
    scheduling algorithms and business logic.

    使用示例 / Usage example::

        class MyTaskService(TaskServiceAsync):
            async def schedule_tasks(self, context):
                # 实现调度逻辑
                # Implement scheduling logic
                ...
    """

    @abc.abstractmethod
    async def schedule_tasks(
        self,
        context: TaskContext,
    ) -> Result[TaskAggregation, str, Err[str]]:
        """调度任务 / Schedule tasks.

        对上下文中的所有任务执行调度，返回聚合结果。
        Schedules all tasks in the context and returns
        an aggregation result.

        Args:
            context: 任务上下文 / Task context.

        Returns:
            调度结果 / Scheduling result.
        """
        ...

    @abc.abstractmethod
    async def validate_task(
        self,
        task: Task,
    ) -> Result[None, str, Err[str]]:
        """验证任务 / Validate a task.

        检查任务参数是否合法。
        Checks whether task parameters are valid.

        Args:
            task: 待验证的任务 / Task to validate.

        Returns:
            验证结果 / Validation result.
        """
        ...

    @abc.abstractmethod
    async def compute_critical_path(
        self,
        tasks: tuple[Task, ...],
    ) -> Result[tuple[str, ...], str, Err[str]]:
        """计算关键路径 / Compute critical path.

        分析任务依赖关系，计算关键路径。
        Analyzes task dependencies and computes the
        critical path.

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            关键路径任务键序列 / Critical path task key sequence.
        """
        ...

    @abc.abstractmethod
    async def estimate_duration(
        self,
        tasks: tuple[Task, ...],
    ) -> Result[float, str, Err[str]]:
        """估算总调度时长 / Estimate total scheduling duration.

        根据任务集合估算完成所有任务所需时间。
        Estimates time needed to complete all tasks
        based on the task collection.

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            估算时长（秒）/ Estimated duration (seconds).
        """
        ...

    async def schedule_single_task(
        self,
        context: TaskContext,
        task_key: str,
    ) -> Result[TaskAggregation, str, Err[str]]:
        """调度单个任务 / Schedule a single task.

        默认实现将单任务包装为上下文后调用 schedule_tasks。
        Default implementation wraps the single task into
        a context and delegates to schedule_tasks.

        Args:
            context: 任务上下文 / Task context.
            task_key: 任务键 / Task key.

        Returns:
            调度结果 / Scheduling result.
        """
        task_result = context.get_or_error(task_key)
        if task_result.is_failed():
            from ospf_python.utils.functional.result import Failed

            err = task_result.error  # type: ignore[attr-defined]
            return Failed(err)
        return await self.schedule_tasks(context)

    async def batch_validate(
        self,
        tasks: tuple[Task, ...],
    ) -> Result[None, str, Err[str]]:
        """批量验证任务 / Batch validate tasks.

        验证所有任务，返回第一个失败的结果。
        Validates all tasks, returning the first failure.

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            验证结果 / Validation result.
        """
        from ospf_python.utils.functional.result import Ok

        for task in tasks:
            result = await self.validate_task(task)
            if result.is_failed():
                return result
        return Ok(None)
