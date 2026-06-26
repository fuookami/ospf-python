"""Task conflict model.

任务冲突模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class ConflictType(Enum):
    """Types of scheduling conflicts.

    调度冲突类型。
    """

    TIME_OVERLAP = "TIME_OVERLAP"
    """Two tasks overlap in time.

    两个任务在时间上重叠。
    """

    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    """Two tasks compete for the same resource.

    两个任务竞争同一资源。
    """

    AIRCRAFT_MISMATCH = "AIRCRAFT_MISMATCH"
    """Assigned aircraft type does not match requirement.

    分配的飞机类型与需求不匹配。
    """

    PRECEDENCE_VIOLATION = "PRECEDENCE_VIOLATION"
    """Task ordering constraint is violated.

    任务顺序约束被违反。
    """


@dataclass(frozen=True)
class TaskConflict:
    """A conflict between two flight tasks.

    两个航班任务之间的冲突。
    """

    task_a: str
    """ID of the first conflicting task.

    第一个冲突任务的 ID。
    """

    task_b: str
    """ID of the second conflicting task.

    第二个冲突任务的 ID。
    """

    conflict_type: ConflictType
    """Type of the conflict.

    冲突类型。
    """

    @property
    def involved_tasks(self) -> tuple[str, str]:
        """Tuple of involved task IDs.

        涉及的任务 ID 元组。
        """
        return (self.task_a, self.task_b)

    @property
    def description(self) -> str:
        """Human-readable conflict description.

        人类可读的冲突描述。
        """
        return f"{self.conflict_type.value}: {self.task_a} <-> {self.task_b}"
