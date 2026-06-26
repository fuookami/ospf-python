"""备份可用性约束 / Backup availability constraint.

确保备份组件处于可用状态。
Ensures backup components are in an available state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.redundancy_result import RedundancyResult

if TYPE_CHECKING:
    from ...model.redundancy_component import RedundancyComponent


@dataclass(frozen=True)
class BackupAvailabilityConstraint:
    """备份可用性约束 / Backup availability constraint.

    校验具有备份的关键组件，其备份组件是否处于活动状态
    且可用度满足最低要求。不可用的备份等同于无备份。
    Validates that backup components of critical components
    are active and meet the minimum availability requirement.
    An unavailable backup is equivalent to no backup.

    Attributes:
        system_id: 系统标识 / System identifier.
        min_availability: 最低可用度要求(0.0~1.0) /
            Minimum availability requirement (0.0~1.0).
    """

    system_id: str = ""
    min_availability: float = 0.99

    def check(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> RedundancyResult:
        """执行备份可用性校验。

        Perform backup availability check.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        critical_ids: list[str] = []

        for comp in components:
            if not comp.is_critical:
                continue

            critical_ids.append(comp.component_id)

            if comp.has_backup and not comp.active:
                violations.append(f"backup_inactive:{comp.component_id}")
                continue

            if comp.has_backup:
                availability = comp.availability
                if availability < self.min_availability:
                    violations.append(
                        f"backup_low_availability:"
                        f"{comp.component_id}:"
                        f"{availability:.4f}<"
                        f"{self.min_availability:.4f}"
                    )

        if violations:
            return RedundancyResult.create_non_compliant(
                system_id=self.system_id,
                redundancy_level=0,
                critical_components=tuple(critical_ids),
                violations=tuple(violations),
            )

        min_backup = min(
            (c.backup_count for c in components if c.is_critical and c.has_backup),
            default=0,
        )
        return RedundancyResult.create_compliant(
            system_id=self.system_id,
            redundancy_level=min_backup,
            critical_components=tuple(critical_ids),
        )

    def is_feasible(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> bool:
        """快速检查备份是否可用。

        Quick check whether backups are available.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            所有备份均可用时返回 True。
            True if all backups are available.
        """
        for comp in components:
            if not comp.is_critical:
                continue
            if comp.has_backup and not comp.active:
                return False
            if comp.has_backup and comp.availability < self.min_availability:
                return False
        return True

    def lowest_availability(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> float:
        """获取最低可用度 / Get lowest availability.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            关键组件中的最低可用度。
            Lowest availability among critical components.
        """
        availabilities = tuple(
            c.availability for c in components if c.is_critical and c.has_backup
        )
        return min(availabilities) if availabilities else 1.0
