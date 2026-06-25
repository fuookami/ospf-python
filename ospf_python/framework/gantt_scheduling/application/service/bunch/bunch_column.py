"""束编组列数据类型 / Bunch column data types.

列生成算法中束编组使用的数据结构。
Data structures used by bunches in the column
generation algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BunchColumn:
    """束编组列 / Bunch column.

    列生成中的一列，表示一种束编组分配模式。
    A column in column generation, representing a bunch
    assignment pattern.

    Attributes:
        bunch_key: 束编组唯一标识 / Bunch unique identifier.
        task_assignments: 任务分配元组，每项为
            (task_key, start_time) / Task assignment tuple,
            each item is (task_key, start_time).
        resource_key: 分配的资源键 / Assigned resource key.
        cost: 列成本 / Column cost.
        reduced_cost: 缩减成本 / Reduced cost.
    """

    bunch_key: str
    task_assignments: tuple[tuple[str, float], ...]
    resource_key: str
    cost: float
    reduced_cost: float = 0.0

    # ==================== 查询 / Queries =========================

    @property
    def task_count(self) -> int:
        """获取任务数量 / Get task count.

        Returns:
            分配中的任务数量 / Number of tasks in assignment.
        """
        return len(self.task_assignments)

    @property
    def task_keys(self) -> tuple[str, ...]:
        """获取所有任务键 / Get all task keys.

        Returns:
            任务键元组 / Task key tuple.
        """
        return tuple(t[0] for t in self.task_assignments)

    @property
    def is_empty(self) -> bool:
        """是否为空列 / Whether empty column.

        Returns:
            无任务分配时返回 True / True when no assignments.
        """
        return len(self.task_assignments) == 0

    def start_time_for(self, task_key: str) -> float:
        """获取指定任务的开始时间 / Get start time for task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            开始时间，未找到时返回 0.0。
            Start time, 0.0 if not found.
        """
        for key, start in self.task_assignments:
            if key == task_key:
                return start
        return 0.0

    def contains_task(self, task_key: str) -> bool:
        """检查是否包含指定任务 / Check if contains a task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            包含该任务时返回 True / True when containing.
        """
        return any(key == task_key for key, _ in self.task_assignments)


@dataclass(frozen=True)
class BunchConstraintCoeff:
    """束编组约束系数记录 / Bunch constraint coefficient record.

    记录束编组变量在约束中的系数和约束元数据。
    Records a bunch variable's coefficient in a constraint
    and the constraint metadata.

    Attributes:
        constraint_name: 约束名称 / Constraint name.
        variable_name: 变量名称 / Variable name.
        coefficient: 系数值 / Coefficient value.
    """

    constraint_name: str
    variable_name: str
    coefficient: float
