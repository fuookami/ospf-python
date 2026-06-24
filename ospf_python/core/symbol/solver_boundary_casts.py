"""求解器边界类型转换 / Solver boundary type casts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.variable.type import VariableType


@dataclass(frozen=True)
class SolverBoundaryCasts:
    """求解器边界类型转换器 / Solver boundary type cast utility.

    在求解器边界条件间进行类型转换。
    Performs type casts between solver boundary conditions.

    Attributes:
        _cast_rules: 类型转换规则 / Type cast rules.
    """

    _cast_rules: dict[str, VariableType] = field(default_factory=dict)
    """类型转换规则 / Type cast rules."""

    def register_cast(
        self,
        source_name: str,
        target_type: VariableType,
    ) -> None:
        """注册类型转换规则 / Register type cast rule.

        Args:
            source_name: 源名称 / Source name.
            target_type: 目标类型 / Target type.
        """
        self._cast_rules[source_name] = target_type

    def lookup_cast(
        self,
        source_name: str,
    ) -> VariableType | None:
        """查找类型转换 / Lookup type cast.

        Args:
            source_name: 源名称 / Source name.

        Returns:
            目标类型或 None / Target type or None.
        """
        return self._cast_rules.get(source_name)

    def has_cast(
        self,
        source_name: str,
    ) -> bool:
        """判断是否有转换规则 / Check if cast rule exists.

        Args:
            source_name: 源名称 / Source name.

        Returns:
            是否存在规则 / Whether the rule exists.
        """
        return source_name in self._cast_rules

    @property
    def rule_count(self) -> int:
        """获取规则数量 / Get rule count.

        Returns:
            转换规则数量 / Number of cast rules.
        """
        return len(self._cast_rules)

    def clear(self) -> None:
        """清空规则 / Clear rules."""
        self._cast_rules.clear()
