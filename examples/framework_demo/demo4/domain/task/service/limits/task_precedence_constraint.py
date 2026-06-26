"""Task precedence constraint.

任务优先约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.task_schedule import TaskSchedule


@dataclass(frozen=True)
class PrecedenceRule:
    """A single precedence ordering rule.

    单条优先顺序规则。
    """

    predecessor_id: str
    """Task that must complete first.

    必须先完成的任务。
    """

    successor_id: str
    """Task that must start after predecessor.

    必须在前序任务之后开始的任务。
    """

    min_gap_minutes: int = 0
    """Minimum gap in minutes between tasks.

    任务之间的最小间隔（分钟）。
    """


class TaskPrecedenceConstraint:
    """Enforces task ordering constraints.

    执行任务顺序约束。
    """

    def __init__(self) -> None:
        """Initialize precedence constraint.

        初始化优先约束。
        """
        self._rules: list[PrecedenceRule] = []

    def add_rule(
        self,
        rule: PrecedenceRule,
    ) -> None:
        """Add a precedence rule.

        添加优先规则。

        Args:
            rule: The precedence rule to add.
        """
        self._rules.append(rule)

    def validate(
        self,
        schedules: Sequence[TaskSchedule],
    ) -> Sequence[str]:
        """Validate schedules against precedence rules.

        根据优先规则验证调度。

        Args:
            schedules: Schedules to validate.

        Returns:
            List of violation descriptions (empty if valid).
        """
        from datetime import timedelta

        schedule_map = {s.task_id: s for s in schedules}
        violations: list[str] = []

        for rule in self._rules:
            pred = schedule_map.get(rule.predecessor_id)
            succ = schedule_map.get(rule.successor_id)
            if pred is None or succ is None:
                continue

            min_start = pred.planned_end + timedelta(minutes=rule.min_gap_minutes)
            if succ.planned_start < min_start:
                violations.append(
                    f"{rule.successor_id} starts before "
                    f"{rule.predecessor_id} completes + "
                    f"{rule.min_gap_minutes}min gap"
                )

        return tuple(violations)

    def is_valid(
        self,
        schedules: Sequence[TaskSchedule],
    ) -> bool:
        """Check if schedules satisfy all precedence rules.

        检查调度是否满足所有优先规则。

        Args:
            schedules: Schedules to check.

        Returns:
            True if all rules are satisfied.
        """
        return len(self.validate(schedules)) == 0

    @property
    def rule_count(self) -> int:
        """Number of registered precedence rules.

        已注册优先规则的数量。
        """
        return len(self._rules)
