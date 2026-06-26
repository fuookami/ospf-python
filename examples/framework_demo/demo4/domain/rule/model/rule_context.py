"""Rule context for managing the rule registry.

规则上下文：管理规则注册表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rule import Rule
    from .rule_type import RuleType


class RuleContext:
    """Registry and lookup service for business rules.

    业务规则的注册表与查询服务。
    """

    def __init__(self) -> None:
        self._registry: dict[str, Rule] = {}

    def register(self, rule: Rule) -> None:
        """Register a rule in the context.

        在上下文中注册一条规则。
        """
        self._registry[rule.rule_id] = rule

    def unregister(self, rule_id: str) -> bool:
        """Remove a rule from the registry. Returns True if found.

        从注册表中移除规则。找到则返回 True。
        """
        if rule_id in self._registry:
            del self._registry[rule_id]
            return True
        return False

    def lookup(self, rule_id: str) -> Rule | None:
        """Look up a rule by its identifier.

        通过标识符查找规则。
        """
        return self._registry.get(rule_id)

    def by_type(
        self,
        rule_type: RuleType,
    ) -> tuple[Rule, ...]:
        """Filter rules by their type.

        按类型筛选规则。
        """
        return tuple(
            rule for rule in self._registry.values() if rule.rule_type == rule_type
        )

    def all_rules(self) -> tuple[Rule, ...]:
        """Return all registered rules.

        返回所有已注册的规则。
        """
        return tuple(self._registry.values())

    @property
    def size(self) -> int:
        """Number of registered rules.

        已注册规则数量。
        """
        return len(self._registry)

    def clear(self) -> None:
        """Remove all registered rules.

        移除所有已注册的规则。
        """
        self._registry.clear()

    def has_rule(self, rule_id: str) -> bool:
        """Check whether a rule is registered.

        检查规则是否已注册。
        """
        return rule_id in self._registry
