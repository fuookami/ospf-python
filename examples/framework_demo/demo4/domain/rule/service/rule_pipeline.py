"""Rule pipeline composing all rule constraints.

规则管道：组合所有规则约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..model.rule_result import RuleResult

if TYPE_CHECKING:
    from .limits.resource_rule_constraint import (
        ResourceRuleConstraint,
    )
    from .limits.scheduling_rule_constraint import (
        SchedulingRuleConstraint,
    )
    from .limits.time_rule_constraint import TimeRuleConstraint


@dataclass(frozen=True)
class PipelineResult:
    """Aggregated result of the rule pipeline.

    规则管道的聚合结果。
    """

    results: tuple[RuleResult, ...]
    all_satisfied: bool


class RulePipeline:
    """Composes rule constraints into a single evaluation pipeline.

    将规则约束组合到单一评估管道中。
    """

    def __init__(
        self,
        *,
        scheduling: SchedulingRuleConstraint,
        resource: ResourceRuleConstraint,
        time: TimeRuleConstraint,
    ) -> None:
        self._scheduling = scheduling
        self._resource = resource
        self._time = time
        self._extra_constraints: list[Any] = []

    def add_constraint(self, constraint: Any) -> None:
        """Append an additional constraint to the pipeline.

        向管道追加额外的约束。
        """
        self._extra_constraints.append(constraint)

    def execute(
        self,
        *,
        tasks: Any = (),
        resources: Any = (),
        slots: Any = (),
    ) -> PipelineResult:
        """Run all constraints and aggregate into results.

        运行所有约束并聚合为结果。
        """
        results: list[RuleResult] = []
        sched_violations = self._scheduling.check(tasks)
        results.append(
            RuleResult(
                rule_id="scheduling_constraint",
                satisfied=len(sched_violations) == 0,
                violations=tuple(sched_violations),
            )
        )
        res_violations = self._resource.check(resources)
        results.append(
            RuleResult(
                rule_id="resource_constraint",
                satisfied=len(res_violations) == 0,
                violations=tuple(res_violations),
            )
        )
        time_violations = self._time.check(slots)
        results.append(
            RuleResult(
                rule_id="time_constraint",
                satisfied=len(time_violations) == 0,
                violations=tuple(time_violations),
            )
        )
        for extra in self._extra_constraints:
            if hasattr(extra, "check"):
                extra_violations = extra.check(
                    tasks=tasks,
                    resources=resources,
                    slots=slots,
                )
                name = type(extra).__name__
                results.append(
                    RuleResult(
                        rule_id=f"extra_{name}",
                        satisfied=len(extra_violations) == 0,
                        violations=tuple(extra_violations),
                    )
                )
        all_ok = all(r.satisfied for r in results)
        return PipelineResult(
            results=tuple(results),
            all_satisfied=all_ok,
        )

    @property
    def scheduling(self) -> SchedulingRuleConstraint:
        """Access the scheduling constraint.

        访问调度约束。
        """
        return self._scheduling

    @property
    def resource(self) -> ResourceRuleConstraint:
        """Access the resource constraint.

        访问资源约束。
        """
        return self._resource

    @property
    def time_constraint(self) -> TimeRuleConstraint:
        """Access the time constraint.

        访问时间约束。
        """
        return self._time
