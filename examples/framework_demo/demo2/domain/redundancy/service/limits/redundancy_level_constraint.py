"""冗余等级约束 / Redundancy level constraint.

确保系统满足最低冗余等级要求。
Ensures the system meets minimum redundancy level
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.redundancy_result import RedundancyResult

if TYPE_CHECKING:
    from ...model.redundancy_component import RedundancyComponent


@dataclass(frozen=True)
class RedundancyLevelConstraint:
    """冗余等级约束 / Redundancy level constraint.

    校验系统中每个关键组件的备份数量是否达到最低要求
    的冗余等级。不满足的组件将被标记为违规。
    Validates that each critical component's backup count
    meets the minimum required redundancy level. Components
    that do not meet the requirement are flagged as violations.

    Attributes:
        system_id: 系统标识 / System identifier.
        min_level: 最低要求冗余等级 /
            Minimum required redundancy level.
    """

    system_id: str = ""
    min_level: int = 1

    def check(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> RedundancyResult:
        """执行冗余等级校验。

        Perform redundancy level check.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        non_compliant_ids: list[str] = []

        for comp in components:
            if comp.is_critical and comp.backup_count < self.min_level:
                violations.append(
                    f"redundancy_below_minimum:"
                    f"{comp.component_id}:"
                    f"{comp.backup_count}<{self.min_level}"
                )
                non_compliant_ids.append(comp.component_id)

        critical_ids = tuple(c.component_id for c in components if c.is_critical)

        if violations:
            actual_min = min(
                (c.backup_count for c in components if c.is_critical),
                default=0,
            )
            return RedundancyResult.create_non_compliant(
                system_id=self.system_id,
                redundancy_level=actual_min,
                critical_components=tuple(non_compliant_ids),
                violations=tuple(violations),
            )

        min_backup = min(
            (c.backup_count for c in components if c.is_critical),
            default=0,
        )
        return RedundancyResult.create_compliant(
            system_id=self.system_id,
            redundancy_level=min_backup,
            critical_components=critical_ids,
        )

    def is_feasible(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> bool:
        """快速检查是否满足冗余等级。

        Quick check whether redundancy level is met.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            所有关键组件均满足要求时返回 True。
            True if all critical components meet requirements.
        """
        return all(
            not c.is_critical or c.backup_count >= self.min_level for c in components
        )
