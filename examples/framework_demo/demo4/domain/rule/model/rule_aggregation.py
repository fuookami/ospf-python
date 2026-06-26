"""Rule aggregation for grouping rules by type.

规则聚合：按类型分组规则。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .rule import HIGH_PRIORITY_THRESHOLD, Rule

if TYPE_CHECKING:
    from .rule_type import RuleType


@dataclass(frozen=True)
class RuleAggregation:
    """Aggregation of rules grouped by their type.

    按类型分组的规则聚合。
    """

    rules: tuple[Rule, ...]
    by_type: dict[RuleType, tuple[Rule, ...]]

    @classmethod
    def from_rules(
        cls,
        rules: tuple[Rule, ...],
    ) -> RuleAggregation:
        """Create aggregation by grouping rules by type.

        通过按类型分组规则来创建聚合。
        """
        groups: dict[RuleType, list[Rule]] = defaultdict(
            list,
        )
        for rule in rules:
            groups[rule.rule_type].append(rule)
        by_type = {rtype: tuple(items) for rtype, items in groups.items()}
        return cls(rules=rules, by_type=by_type)

    @property
    def high_priority_rules(self) -> tuple[Rule, ...]:
        """Rules with priority at or above the threshold.

        优先级达到或超过阈值的规则。
        """
        return tuple(r for r in self.rules if r.priority >= HIGH_PRIORITY_THRESHOLD)

    @property
    def count(self) -> int:
        """Total number of rules.

        规则总数。
        """
        return len(self.rules)

    @property
    def type_counts(self) -> dict[RuleType, int]:
        """Count of rules per type.

        每种类型的规则数量。
        """
        return {rtype: len(items) for rtype, items in self.by_type.items()}

    def for_type(
        self,
        rule_type: RuleType,
    ) -> tuple[Rule, ...]:
        """Get all rules of a specific type.

        获取特定类型的所有规则。
        """
        return self.by_type.get(rule_type, ())
