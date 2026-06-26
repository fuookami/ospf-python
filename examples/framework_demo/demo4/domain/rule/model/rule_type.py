"""Rule type enumeration.

规则类型枚举 / Rule type enumeration.
"""

from __future__ import annotations

from enum import StrEnum


class RuleType(StrEnum):
    """Classification of business rules for scheduling.

    调度业务规则的分类。
    """

    SCHEDULING = "SCHEDULING"
    RESOURCE = "RESOURCE"
    TIME = "TIME"
    PRIORITY = "PRIORITY"
    CONFLICT = "CONFLICT"

    @property
    def description(self) -> str:
        """Bilingual description of the rule type.

        规则类型的中英文描述。
        """
        descriptions: dict[RuleType, str] = {
            RuleType.SCHEDULING: (
                "调度规则：约束任务分配 / Scheduling: constrain task assignment"
            ),
            RuleType.RESOURCE: (
                "资源规则：约束资源使用 / Resource: constrain resource usage"
            ),
            RuleType.TIME: ("时间规则：约束时间窗口 / Time: constrain time windows"),
            RuleType.PRIORITY: (
                "优先级规则：约束优先顺序 / Priority: constrain ordering"
            ),
            RuleType.CONFLICT: (
                "冲突规则：禁止冲突组合 / Conflict: forbid conflicting combos"
            ),
        }
        return descriptions[self]
