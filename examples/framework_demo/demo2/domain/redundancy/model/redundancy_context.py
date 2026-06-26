"""冗余分析上下文 / Redundancy analysis context.

管理冗余分析的注册与验证流程。
Manages registration and validation for redundancy analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .redundancy_aggregation import RedundancyAggregation
from .redundancy_result import RedundancyResult

if TYPE_CHECKING:
    from .redundancy_component import RedundancyComponent


@dataclass
class RedundancyContext:
    """冗余分析上下文 / Redundancy analysis context.

    提供可变的注册接口，收集所有冗余组件和分析结果后
    可生成不可变的聚合对象并执行验证。
    Provides a mutable registration interface; after
    collecting all redundancy components and analysis results,
    generates an immutable aggregation object and performs
    validation.

    Attributes:
        _components: 已注册组件 / Registered components.
        _results: 已注册结果 / Registered results.
        _min_required_level: 最低要求冗余等级 /
            Minimum required redundancy level.
    """

    _components: list[RedundancyComponent] = field(
        default_factory=list,
        init=False,
    )
    _results: list[RedundancyResult] = field(
        default_factory=list,
        init=False,
    )
    _min_required_level: int = field(
        default=1,
        init=False,
    )

    def register_component(
        self,
        component: RedundancyComponent,
    ) -> None:
        """注册冗余组件 / Register redundancy component.

        Args:
            component: 冗余组件 / Redundancy component.
        """
        self._components.append(component)

    def register_result(
        self,
        result: RedundancyResult,
    ) -> None:
        """注册冗余结果 / Register redundancy result.

        Args:
            result: 冗余结果 / Redundancy result.
        """
        self._results.append(result)

    def set_min_required_level(self, level: int) -> None:
        """设置最低要求冗余等级。

        Set minimum required redundancy level.

        Args:
            level: 最低要求等级 / Minimum required level.
        """
        self._min_required_level = max(0, level)

    @property
    def min_required_level(self) -> int:
        """最低要求冗余等级 / Min required level."""
        return self._min_required_level

    @property
    def component_count(self) -> int:
        """已注册组件数 / Registered component count."""
        return len(self._components)

    @property
    def result_count(self) -> int:
        """已注册结果数 / Registered result count."""
        return len(self._results)

    @property
    def critical_component_count(self) -> int:
        """关键组件数 / Critical component count."""
        return sum(1 for c in self._components if c.is_critical)

    def find_component(
        self,
        component_id: str,
    ) -> RedundancyComponent | None:
        """按标识查找组件。

        Find component by identifier.

        Args:
            component_id: 组件标识 / Component identifier.

        Returns:
            匹配的组件或 None。
            Matching component, or None.
        """
        for c in self._components:
            if c.component_id == component_id:
                return c
        return None

    def build_aggregation(self) -> RedundancyAggregation:
        """构建不可变聚合对象。

        Build an immutable aggregation object from
        the currently registered data.

        Returns:
            包含所有已注册数据的聚合对象。
            Aggregation object with all registered data.
        """
        return RedundancyAggregation(
            results=tuple(self._results),
            components=tuple(self._components),
        )

    def validate(self) -> RedundancyResult:
        """执行基础验证 / Perform basic validation.

        检查关键组件是否具有足够备份。
        Checks whether critical components have
        sufficient backups.

        Returns:
            验证结果 / Validation result.
        """
        violations: list[str] = []
        critical_ids: list[str] = []

        for comp in self._components:
            if comp.is_critical:
                critical_ids.append(comp.component_id)
                if comp.backup_count < self._min_required_level:
                    violations.append(
                        f"insufficient_backup:"
                        f"{comp.component_id}:"
                        f"{comp.backup_count}<{self._min_required_level}"
                    )

        if violations:
            return RedundancyResult.create_non_compliant(
                system_id="context_validation",
                redundancy_level=min(
                    c.backup_count for c in self._components if c.is_critical
                )
                if critical_ids
                else 0,
                critical_components=tuple(critical_ids),
                violations=tuple(violations),
            )

        min_level = min(
            (c.backup_count for c in self._components if c.is_critical),
            default=0,
        )
        return RedundancyResult.create_compliant(
            system_id="context_validation",
            redundancy_level=min_level,
            critical_components=tuple(critical_ids),
        )
