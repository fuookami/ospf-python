"""束编组调度问题定义 / Bunch scheduling problem definition.

封装束编组的调度输入数据，包括任务集合、资源和容量。
Encapsulates scheduling input data for a bunch, including
task set, resource, and capacity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchProblem:
    """束编组调度问题 / Bunch scheduling problem.

    描述一个束编组的完整参数，束编组是分配到同一资源上
    的一组任务。用于列生成中的定价子问题。
    Describes the complete parameters of a bunch, which is
    a group of tasks assigned to the same resource. Used in
    column generation pricing subproblems.

    Attributes:
        bunch_key: 束编组唯一标识 / Unique bunch identifier.
        task_keys: 包含的任务键元组 / Tuple of contained
            task keys.
        resource_key: 分配的资源键 / Assigned resource key.
        capacity: 容量上限 / Capacity upper bound.
        cost: 束编组成本 / Bunch cost.
    """

    bunch_key: str = ""
    task_keys: tuple[str, ...] = ()
    resource_key: str = ""
    capacity: float = 0.0
    cost: float = 0.0

    # ==================== 查询 / Queries =========================

    @property
    def task_count(self) -> int:
        """获取任务数量 / Get task count.

        Returns:
            束编组中任务的数量 / Number of tasks in bunch.
        """
        return len(self.task_keys)

    @property
    def is_empty(self) -> bool:
        """是否为空束编组 / Whether empty bunch.

        Returns:
            无任务时返回 True / True when no tasks.
        """
        return len(self.task_keys) == 0

    @property
    def has_resource(self) -> bool:
        """是否已指定资源 / Whether resource is specified.

        Returns:
            资源键非空时返回 True / True when resource key
            is non-empty.
        """
        return len(self.resource_key) > 0

    def contains_task(self, task_key: str) -> bool:
        """检查是否包含指定任务 / Check if contains a task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            包含该任务时返回 True / True when containing.
        """
        return task_key in self.task_keys

    def task_index(self, task_key: str) -> int:
        """获取任务在束编组中的索引 / Get task index in bunch.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            任务索引，不存在时返回 -1。
            Task index, -1 if not found.
        """
        for idx, key in enumerate(self.task_keys):
            if key == task_key:
                return idx
        return -1

    def without_task(self, task_key: str) -> BunchProblem:
        """创建移除指定任务后的副本。

        Create a copy with the specified task removed.

        Args:
            task_key: 要移除的任务键 / Task key to remove.

        Returns:
            移除任务后的新束编组问题 / New bunch problem
            with the task removed.
        """
        return BunchProblem(
            bunch_key=self.bunch_key,
            task_keys=tuple(k for k in self.task_keys if k != task_key),
            resource_key=self.resource_key,
            capacity=self.capacity,
            cost=self.cost,
        )
