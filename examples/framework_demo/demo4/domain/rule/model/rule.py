"""Rule model for business rule definitions.

规则模型：业务规则定义。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .rule_type import RuleType

HIGH_PRIORITY_THRESHOLD: int = 8


@dataclass(frozen=True)
class Rule:
    """A business rule applicable to scheduling.

    适用于调度的业务规则。
    """

    rule_id: str
    rule_type: RuleType
    parameters: dict[str, Any]
    priority: int

    @property
    def is_high_priority(self) -> bool:
        """Whether this rule is high priority.

        此规则是否为高优先级。
        """
        return self.priority >= HIGH_PRIORITY_THRESHOLD

    @property
    def display_name(self) -> str:
        """Human-readable display name for the rule.

        规则的人类可读显示名称。
        """
        return f"[{self.rule_type.value}] {self.rule_id} (P{self.priority})"

    def has_parameter(self, key: str) -> bool:
        """Check whether a parameter key exists.

        检查参数键是否存在。
        """
        return key in self.parameters

    def get_parameter(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve a parameter value with a default.

        检索参数值并提供默认值。
        """
        return self.parameters.get(key, default)

    def applies_to_resource(
        self,
        resource_type: str,
    ) -> bool:
        """Check whether this rule applies to a resource type.

        检查此规则是否适用于某资源类型。
        """
        target = self.parameters.get("resource_type")
        if target is None:
            return True
        return bool(target == resource_type)
