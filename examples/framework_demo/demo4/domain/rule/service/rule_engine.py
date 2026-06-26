"""Rule engine for evaluating rules against schedules.

规则引擎：对调度评估规则。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..model.rule_result import RuleResult
from ..model.rule_type import RuleType

if TYPE_CHECKING:
    from ..model.rule import Rule
    from ..model.rule_context import RuleContext


@dataclass(frozen=True)
class ScheduleView:
    """View of a schedule for rule evaluation.

    用于规则评估的调度视图。
    """

    tasks: tuple[dict[str, Any], ...]
    resources: tuple[dict[str, Any], ...]
    time_slots: tuple[dict[str, Any], ...]


class RuleEngine:
    """Evaluates registered rules against a schedule view.

    对调度视图评估已注册的规则。
    """

    def __init__(self, context: RuleContext) -> None:
        self._context = context

    def evaluate(
        self,
        schedule: ScheduleView,
    ) -> tuple[RuleResult, ...]:
        """Evaluate all registered rules against the schedule.

        对调度评估所有已注册规则。
        """
        results: list[RuleResult] = []
        for rule in self._context.all_rules():
            result = self._evaluate_rule(rule, schedule)
            results.append(result)
        return tuple(results)

    def evaluate_by_type(
        self,
        rule_type: RuleType,
        schedule: ScheduleView,
    ) -> tuple[RuleResult, ...]:
        """Evaluate only rules of a specific type.

        仅评估特定类型的规则。
        """
        rules = self._context.by_type(rule_type)
        return tuple(self._evaluate_rule(r, schedule) for r in rules)

    def _evaluate_rule(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> RuleResult:
        """Evaluate a single rule against the schedule.

        对调度评估单条规则。
        """
        violations: list[str] = []
        if rule.rule_type == RuleType.SCHEDULING:
            violations.extend(
                self._check_scheduling(rule, schedule),
            )
        elif rule.rule_type == RuleType.RESOURCE:
            violations.extend(
                self._check_resource(rule, schedule),
            )
        elif rule.rule_type == RuleType.TIME:
            violations.extend(
                self._check_time(rule, schedule),
            )
        elif rule.rule_type == RuleType.PRIORITY:
            violations.extend(
                self._check_priority(rule, schedule),
            )
        elif rule.rule_type == RuleType.CONFLICT:
            violations.extend(
                self._check_conflict(rule, schedule),
            )
        return RuleResult(
            rule_id=rule.rule_id,
            satisfied=len(violations) == 0,
            violations=tuple(violations),
        )

    def _check_scheduling(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> list[str]:
        """Check scheduling-specific rule conditions.

        检查调度特定的规则条件。
        """
        violations: list[str] = []
        resource_filter = rule.get_parameter(
            "resource_type",
        )
        for task in schedule.tasks:
            if resource_filter and task.get("resource_type") != resource_filter:
                continue
            max_tasks = rule.get_parameter(
                "max_tasks_per_slot",
                0,
            )
            if max_tasks > 0:
                violations.extend(
                    self._check_slot_capacity(
                        task,
                        schedule.time_slots,
                        max_tasks,
                    ),
                )
        return violations

    def _check_resource(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> list[str]:
        """Check resource-specific rule conditions.

        检查资源特定的规则条件。
        """
        violations: list[str] = []
        max_capacity = rule.get_parameter(
            "max_capacity",
            0,
        )
        for resource in schedule.resources:
            usage = resource.get("current_usage", 0)
            if max_capacity > 0 and usage > max_capacity:
                violations.append(
                    f"Resource '{resource.get('name')}' "
                    f"usage {usage} exceeds "
                    f"capacity {max_capacity}"
                )
        return violations

    def _check_time(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> list[str]:
        """Check time-specific rule conditions.

        检查时间特定的规则条件。
        """
        violations: list[str] = []
        min_gap = rule.get_parameter(
            "min_gap_seconds",
            0.0,
        )
        sorted_slots = sorted(
            schedule.time_slots,
            key=lambda s: s.get("start_time", 0.0),
        )
        for left, right in zip(
            sorted_slots,
            sorted_slots[1:],
            strict=False,
        ):
            gap = right.get("start_time", 0.0) - left.get("end_time", 0.0)
            if min_gap > 0 and 0 < gap < min_gap:
                violations.append(
                    f"Gap {gap:.1f}s between slots below minimum {min_gap:.1f}s"
                )
        return violations

    def _check_priority(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> list[str]:
        """Check priority-specific rule conditions.

        检查优先级特定的规则条件。
        """
        violations: list[str] = []
        enforce_order = rule.get_parameter(
            "enforce_priority_order",
            False,
        )
        if enforce_order:
            sorted_tasks = sorted(
                schedule.tasks,
                key=lambda t: t.get("start_time", 0.0),
            )
            for left, right in zip(
                sorted_tasks,
                sorted_tasks[1:],
                strict=False,
            ):
                lp = left.get("priority", 0)
                rp = right.get("priority", 0)
                if lp > rp:
                    violations.append(
                        f"Higher priority task "
                        f"'{left.get('id')}' (P{lp}) "
                        f"scheduled after lower "
                        f"'{right.get('id')}' (P{rp})"
                    )
        return violations

    def _check_conflict(
        self,
        rule: Rule,
        schedule: ScheduleView,
    ) -> list[str]:
        """Check conflict-specific rule conditions.

        检查冲突特定的规则条件。
        """
        violations: list[str] = []
        forbidden = rule.get_parameter(
            "forbidden_pairs",
            (),
        )
        task_resources: dict[str, str] = {
            t.get("id", ""): t.get("resource_type", "") for t in schedule.tasks
        }
        for pair in forbidden:
            if isinstance(pair, (list, tuple)):
                t1, t2 = pair[0], pair[1]
                r1 = task_resources.get(t1, "")
                r2 = task_resources.get(t2, "")
                if r1 and r2 and r1 == r2:
                    violations.append(
                        f"Conflicting tasks '{t1}' and '{t2}' share resource '{r1}'"
                    )
        return violations

    def _check_slot_capacity(
        self,
        task: dict[str, Any],
        slots: tuple[dict[str, Any], ...],
        max_tasks: int,
    ) -> list[str]:
        """Check if a slot exceeds the max task count.

        检查时间槽是否超过最大任务数。
        """
        violations: list[str] = []
        task_start = task.get("start_time", 0.0)
        task_end = task.get("end_time", 0.0)
        for slot in slots:
            slot_start = slot.get("start_time", 0.0)
            slot_end = slot.get("end_time", 0.0)
            if task_start < slot_end and slot_start < task_end:
                count = slot.get("task_count", 0)
                if count > max_tasks:
                    violations.append(
                        f"Slot at {slot_start}-{slot_end}"
                        f" has {count} tasks "
                        f"(max {max_tasks})"
                    )
        return violations
