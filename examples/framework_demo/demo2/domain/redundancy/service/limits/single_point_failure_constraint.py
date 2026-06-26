"""单点故障约束 / Single point of failure constraint.

确保系统中不存在单点故障。
Ensures that no single point of failure exists in the system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.redundancy_result import RedundancyResult

if TYPE_CHECKING:
    from ...model.redundancy_component import RedundancyComponent


@dataclass(frozen=True)
class SinglePointFailureConstraint:
    """单点故障约束 / Single point of failure constraint.

    校验系统中的关键组件是否均具有备份，消除单点故障。
    针对每个关键组件检查备份数量，若关键组件无备份
    则判定为单点故障。
    Validates that all critical components in the system
    have backups, eliminating single points of failure.
    Checks backup count for each critical component; a
    critical component without backup is flagged as a
    single point of failure.

    Attributes:
        system_id: 系统标识 / System identifier.
    """

    system_id: str = ""

    def check(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> RedundancyResult:
        """执行单点故障校验。

        Perform single point of failure check.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        spof_components: list[str] = []

        for comp in components:
            if comp.is_critical and not comp.has_backup:
                violations.append(
                    f"single_point_of_failure:{comp.component_id}:no_backup"
                )
                spof_components.append(comp.component_id)

        critical_ids = tuple(c.component_id for c in components if c.is_critical)

        if violations:
            return RedundancyResult.create_non_compliant(
                system_id=self.system_id,
                redundancy_level=0,
                critical_components=tuple(spof_components),
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
        """快速检查是否无单点故障。

        Quick check whether there are no single points
        of failure.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            无单点故障时返回 True。
            True if no single point of failure exists.
        """
        return all(not (c.is_critical and not c.has_backup) for c in components)

    def count_spof(
        self,
        components: tuple[RedundancyComponent, ...],
    ) -> int:
        """统计单点故障数量 / Count single points of failure.

        Args:
            components: 系统组件列表 / System component list.

        Returns:
            单点故障组件数量 / Number of SPOF components.
        """
        return sum(1 for c in components if c.is_critical and not c.has_backup)
