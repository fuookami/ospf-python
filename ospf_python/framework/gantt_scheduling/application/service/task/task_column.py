"""调度列数据类型 / Scheduling column data types.

列生成算法中使用的数据结构。
Data structures used in the column generation algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskColumn:
    """调度列 / Scheduling column.

    列生成中的一列，表示一种任务分配模式。
    A column in column generation, representing a task
    assignment pattern.

    Attributes:
        column_key: 列唯一标识 / Column unique identifier.
        task_assignments: 任务分配元组，每项为
            (task_key, resource_key, start_time) /
            Task assignment tuple, each item is
            (task_key, resource_key, start_time).
        cost: 列成本 / Column cost.
        reduced_cost: 缩减成本 / Reduced cost.
    """

    column_key: str
    task_assignments: tuple[tuple[str, str, float], ...]
    cost: float
    reduced_cost: float = 0.0


@dataclass(frozen=True)
class ConstraintCoeff:
    """约束系数记录 / Constraint coefficient record.

    记录变量在约束中的系数和约束元数据。
    Records a variable's coefficient in a constraint
    and the constraint metadata.

    Attributes:
        constraint_name: 约束名称 / Constraint name.
        variable_name: 变量名称 / Variable name.
        coefficient: 系数值 / Coefficient value.
    """

    constraint_name: str
    variable_name: str
    coefficient: float
