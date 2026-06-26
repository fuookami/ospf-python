"""软安全措施模型 / Soft security measure model.

定义单个软安全措施的数据结构。
Defines the data structure for a single soft security measure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MeasureType(Enum):
    """措施类型 / Measure type.

    分类软安全措施的业务类别。
    Classifies business categories of soft security measures.
    """

    ACCESS_CONTROL = "access_control"
    """访问控制 / Access control."""

    SURVEILLANCE = "surveillance"
    """监控覆盖 / Surveillance coverage."""

    BAGGAGE_SCREENING = "baggage_screening"
    """行李安检 / Baggage screening."""

    PERSONNEL_VETTING = "personnel_vet"
    """人员审查 / Personnel vetting."""

    CYBER_DEFENSE = "cyber_defense"
    """网络防御 / Cyber defense."""


@dataclass(frozen=True)
class SoftSecurityMeasure:
    """软安全措施 / Soft security measure.

    表示一项已实施或待评估的安全措施，包含其类型、
    有效性和成本信息。
    Represents an implemented or pending security measure,
    including its type, effectiveness, and cost.

    Attributes:
        measure_id: 措施唯一标识 / Unique measure identifier.
        measure_type: 措施类别 / Measure category.
        effectiveness: 有效性评分 (0.0~1.0) /
            Effectiveness score (0.0~1.0).
        cost: 实施成本 / Implementation cost.
        zone: 所属区域标识 / Affiliated zone identifier.
        active: 是否已激活 / Whether the measure is active.
    """

    measure_id: str
    measure_type: MeasureType
    effectiveness: float
    cost: float
    zone: str = ""
    active: bool = True

    @property
    def is_effective(self) -> bool:
        """是否有效 / Is effective.

        Returns:
            有效性 >= 0.7 时返回 True。
            True if effectiveness >= 0.7.
        """
        return self.effectiveness >= 0.7

    @property
    def cost_efficiency(self) -> float:
        """成本效率 / Cost efficiency.

        Returns:
            有效性与成本之比，成本为零时返回 0.0。
            Ratio of effectiveness to cost; 0.0 if cost is zero.
        """
        if self.cost <= 0.0:
            return 0.0
        return self.effectiveness / self.cost

    def deactivate(self) -> SoftSecurityMeasure:
        """停用措施 / Deactivate measure.

        Returns:
            停用后的新措施实例。
            New measure instance with active=False.
        """
        return SoftSecurityMeasure(
            measure_id=self.measure_id,
            measure_type=self.measure_type,
            effectiveness=self.effectiveness,
            cost=self.cost,
            zone=self.zone,
            active=False,
        )

    def with_effectiveness(
        self,
        new_effectiveness: float,
    ) -> SoftSecurityMeasure:
        """更新有效性 / Update effectiveness.

        Args:
            new_effectiveness: 新有效性值 / New effectiveness value.

        Returns:
            更新后的新措施实例。
            New measure with updated effectiveness.
        """
        clamped = min(1.0, max(0.0, new_effectiveness))
        return SoftSecurityMeasure(
            measure_id=self.measure_id,
            measure_type=self.measure_type,
            effectiveness=clamped,
            cost=self.cost,
            zone=self.zone,
            active=self.active,
        )
