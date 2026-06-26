"""Rule evaluation result model.

规则评估结果模型 / Rule evaluation result model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    """Result of evaluating a single rule against a schedule.

    对调度评估单条规则的结果。
    """

    rule_id: str
    satisfied: bool
    violations: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """Whether the rule has no violations.

        规则是否没有违规。
        """
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        """Number of violations found.

        发现的违规数量。
        """
        return len(self.violations)

    def summary(self) -> str:
        """Human-readable summary of the result.

        结果的人类可读摘要。
        """
        status = "PASS" if self.satisfied else "FAIL"
        count = self.violation_count
        return f"[{status}] Rule '{self.rule_id}': {count} violations"

    def merge(self, other: RuleResult) -> RuleResult:
        """Merge two results for the same rule.

        合并同一规则的两个结果。
        """
        return RuleResult(
            rule_id=self.rule_id,
            satisfied=self.satisfied and other.satisfied,
            violations=self.violations + other.violations,
        )
