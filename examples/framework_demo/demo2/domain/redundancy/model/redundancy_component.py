"""冗余组件 / Redundancy component.

定义系统冗余分析中的组件数据结构。
Defines the component data structure for system
redundancy analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RedundancyComponent:
    """冗余组件 / Redundancy component.

    描述系统中的一个组件及其冗余配置。
    Describes a component in a system and its redundancy
    configuration.

    Attributes:
        component_id: 组件标识 / Component identifier.
        is_critical: 是否为关键组件 /
            Whether the component is critical.
        backup_count: 备份组件数量 /
            Number of backup components.
        mtbf: 平均故障间隔时间(小时) /
            Mean time between failures (hours).
        active: 是否处于活动状态 /
            Whether the component is active.
    """

    component_id: str
    is_critical: bool = False
    backup_count: int = 0
    mtbf: float = 0.0
    active: bool = True

    @property
    def has_backup(self) -> bool:
        """是否有备份 / Has backup.

        Returns:
            备份数量大于 0 时返回 True。
            True if backup count is greater than 0.
        """
        return self.backup_count > 0

    @property
    def total_instances(self) -> int:
        """总实例数(含主组件) / Total instances (incl. primary).

        Returns:
            备份数加 1 / Backup count plus 1.
        """
        return self.backup_count + 1

    @property
    def redundancy_level(self) -> int:
        """该组件的冗余等级 / Component redundancy level.

        Returns:
            0=无冗余, 1=单冗余, 2=双冗余, 3+=三冗余以上。
            0=none, 1=single, 2=double, 3+=triple+.
        """
        return self.backup_count

    @property
    def availability(self) -> float:
        """组件可用度 / Component availability.

        基于简化的可用度公式: A = 1 - (1-A0)^(n+1)
        其中 A0 = MTBF / (MTBF + MTTR)，MTTR 假设为 1 小时。
        Based on simplified availability formula.
        """
        if self.mtbf <= 0.0:
            return 0.0
        mttr = 1.0
        single_availability = self.mtbf / (self.mtbf + mttr)
        unavailability = 1.0 - single_availability
        total = self.total_instances
        return 1.0 - unavailability**total

    @staticmethod
    def create_critical(
        *,
        component_id: str,
        backup_count: int = 1,
        mtbf: float = 1000.0,
    ) -> RedundancyComponent:
        """创建关键组件 / Create critical component.

        Args:
            component_id: 组件标识 / Component identifier.
            backup_count: 备份数 / Backup count.
            mtbf: 平均故障间隔(小时) / MTBF (hours).

        Returns:
            关键组件实例 / Critical component instance.
        """
        return RedundancyComponent(
            component_id=component_id,
            is_critical=True,
            backup_count=backup_count,
            mtbf=mtbf,
            active=True,
        )

    @staticmethod
    def create_non_critical(
        *,
        component_id: str,
        mtbf: float = 500.0,
    ) -> RedundancyComponent:
        """创建非关键组件 / Create non-critical component.

        Args:
            component_id: 组件标识 / Component identifier.
            mtbf: 平均故障间隔(小时) / MTBF (hours).

        Returns:
            非关键组件实例 / Non-critical component instance.
        """
        return RedundancyComponent(
            component_id=component_id,
            is_critical=False,
            backup_count=0,
            mtbf=mtbf,
            active=True,
        )
