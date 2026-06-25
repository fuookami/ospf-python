"""任务聚合模型 / Task aggregation model.

管理迭代列生成过程中的任务集合。
Manages task collections during iterative column generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
        Task,
    )


@dataclass(frozen=True)
class TaskAggregation:
    """任务聚合 / Task aggregation.

    聚合多次迭代产生的任务集合，维护关键路径和总时长。
    在列生成算法中用于跟踪已生成的任务列。
    Aggregates task sets produced across iterations,
    maintaining critical path and total duration.
    Used in column generation to track generated columns.

    Attributes:
        tasks: 所有任务元组 / All task tuple.
        total_duration: 总持续时长 / Total duration.
        critical_path: 关键路径任务键序列 / Critical path
            task key sequence.
    """

    tasks: tuple[Task, ...] = ()
    total_duration: float = 0.0
    critical_path: tuple[str, ...] = ()

    @staticmethod
    def create(
        *,
        tasks: tuple[Task, ...] = (),
    ) -> TaskAggregation:
        """工厂方法创建聚合 / Factory to create aggregation.

        自动计算总时长和关键路径。
        Automatically computes total duration and critical path.

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            新的聚合实例 / New aggregation instance.
        """
        total = TaskAggregation._compute_total_duration(tasks)
        critical = TaskAggregation._compute_critical_path(tasks)
        return TaskAggregation(
            tasks=tasks,
            total_duration=total,
            critical_path=critical,
        )

    @staticmethod
    def empty() -> TaskAggregation:
        """创建空聚合 / Create empty aggregation.

        Returns:
            空聚合实例 / Empty aggregation instance.
        """
        return TaskAggregation(
            tasks=(),
            total_duration=0.0,
            critical_path=(),
        )

    @property
    def size(self) -> int:
        """任务数量 / Task count.

        Returns:
            任务总数 / Total task count.
        """
        return len(self.tasks)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无任务时返回 True。
            True when no tasks.
        """
        return len(self.tasks) == 0

    @property
    def task_keys(self) -> tuple[str, ...]:
        """获取所有任务键 / Get all task keys.

        Returns:
            任务键元组 / Task key tuple.
        """
        return tuple(t.task_key for t in self.tasks)

    @property
    def critical_path_length(self) -> int:
        """关键路径长度 / Critical path length.

        Returns:
            关键路径上的任务数。
            Number of tasks on critical path.
        """
        return len(self.critical_path)

    def add_tasks(
        self,
        new_tasks: tuple[Task, ...],
    ) -> TaskAggregation:
        """添加任务并返回新聚合 / Add tasks and return new aggregation.

        去除重复任务键后合并。
        Merges after deduplicating by task key.

        Args:
            new_tasks: 要添加的新任务 / New tasks to add.

        Returns:
            包含所有任务的新聚合 / New aggregation with all tasks.
        """
        existing_keys = {t.task_key for t in self.tasks}
        unique_new = tuple(t for t in new_tasks if t.task_key not in existing_keys)
        all_tasks = self.tasks + unique_new
        return TaskAggregation.create(tasks=all_tasks)

    def remove_task(
        self,
        task_key: str,
    ) -> TaskAggregation:
        """移除任务并返回新聚合 / Remove task and return new aggregation.

        Args:
            task_key: 要移除的任务键 / Task key to remove.

        Returns:
            移除后的新聚合 / New aggregation after removal.
        """
        remaining = tuple(t for t in self.tasks if t.task_key != task_key)
        return TaskAggregation.create(tasks=remaining)

    def get_task(self, task_key: str) -> Task | None:
        """按键获取任务 / Get task by key.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            任务或 None / Task or None.
        """
        for task in self.tasks:
            if task.task_key == task_key:
                return task
        return None

    def contains(self, task_key: str) -> bool:
        """检查是否包含任务 / Check if contains task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            是否包含 / Whether contains.
        """
        return any(t.task_key == task_key for t in self.tasks)

    def with_critical_path(
        self,
        path: tuple[str, ...],
    ) -> TaskAggregation:
        """创建不同关键路径的新聚合 / Create aggregation with different critical path.

        Args:
            path: 新关键路径 / New critical path.

        Returns:
            新聚合实例 / New aggregation instance.
        """
        return TaskAggregation(
            tasks=self.tasks,
            total_duration=self.total_duration,
            critical_path=path,
        )

    @staticmethod
    def _compute_total_duration(tasks: tuple[Task, ...]) -> float:
        """计算任务总持续时长 / Compute total task duration.

        按最长路径计算（考虑依赖关系）。
        Computed via longest path (considering dependencies).

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            总持续时长 / Total duration.
        """
        if not tasks:
            return 0.0

        # 按最早开始时间排序
        sorted_tasks = sorted(tasks, key=lambda t: t.earliest_start)

        # 计算关键路径长度：动态规划求最长路径
        # 关键路径 = 从最早任务到最晚结束的最长路径
        max_end = 0.0
        for task in sorted_tasks:
            task_end = max(task.earliest_start, max_end) + task.duration
            max_end = max(max_end, task_end)

        min_start = sorted_tasks[0].earliest_start
        return max_end - min_start

    @staticmethod
    def _compute_critical_path(
        tasks: tuple[Task, ...],
    ) -> tuple[str, ...]:
        """计算关键路径 / Compute critical path.

        使用贪心策略识别关键路径上的任务。
        Uses greedy strategy to identify tasks on critical path.

        Args:
            tasks: 任务集合 / Task collection.

        Returns:
            关键路径任务键序列 / Critical path task key sequence.
        """
        if not tasks:
            return ()

        # 按 slack 排序，slack 为 0 的任务在关键路径上
        critical = sorted(tasks, key=lambda t: t.slack)
        result: list[str] = []
        for task in critical:
            if task.slack == 0.0:
                result.append(task.task_key)

        # 若无 slack=0 的任务，选取持续时间最长的任务
        if not result:
            longest = max(tasks, key=lambda t: t.duration)
            result.append(longest.task_key)

        return tuple(result)
