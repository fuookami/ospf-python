"""Scheduling rule constraint enforcement.

调度规则约束执行 / Scheduling rule constraint enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskView:
    """View of a task for constraint checking.

    用于约束检查的任务视图。
    """

    task_id: str
    resource_type: str
    start_time: float
    end_time: float


class SchedulingRuleConstraint:
    """Enforces scheduling rules on task assignments.

    强制执行任务分配的调度规则。
    """

    def __init__(
        self,
        *,
        max_overlap: int = 0,
        enforce_ordering: bool = True,
    ) -> None:
        self._max_overlap = max_overlap
        self._enforce_ordering = enforce_ordering

    def check(
        self,
        tasks: tuple[TaskView, ...],
    ) -> list[str]:
        """Validate scheduling rules against tasks.

        对任务验证调度规则。
        """
        violations: list[str] = []
        violations.extend(
            self._check_overlaps(tasks),
        )
        if self._enforce_ordering:
            violations.extend(
                self._check_ordering(tasks),
            )
        return violations

    def _check_overlaps(
        self,
        tasks: tuple[TaskView, ...],
    ) -> list[str]:
        """Check for overlapping tasks on the same resource.

        检查同一资源上的重叠任务。
        """
        violations: list[str] = []
        by_resource: dict[str, list[TaskView]] = {}
        for task in tasks:
            by_resource.setdefault(
                task.resource_type,
                [],
            ).append(task)
        for res_type, group in by_resource.items():
            sorted_group = sorted(
                group,
                key=lambda t: t.start_time,
            )
            for i, left in enumerate(sorted_group):
                overlap_count = 0
                for right in sorted_group[i + 1 :]:
                    if right.start_time < left.end_time:
                        overlap_count += 1
                if overlap_count > self._max_overlap:
                    violations.append(
                        f"Task '{left.task_id}' on "
                        f"'{res_type}' has "
                        f"{overlap_count} overlaps "
                        f"(max {self._max_overlap})"
                    )
        return violations

    def _check_ordering(
        self,
        tasks: tuple[TaskView, ...],
    ) -> list[str]:
        """Check that task start times are well-ordered.

        检查任务开始时间是否有序。
        """
        violations: list[str] = []
        for task in tasks:
            if task.start_time > task.end_time:
                violations.append(
                    f"Task '{task.task_id}' has "
                    f"start ({task.start_time}) "
                    f"> end ({task.end_time})"
                )
        return violations
