"""温控货物约束 / Temperature control constraint.

验证温控货物是否满足货舱温度范围要求。
Validates that temperature-controlled cargo meets
the cargo hold temperature range requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...model.airworthiness_result import AirworthinessResult


class TempZone(Enum):
    """温度区域 / Temperature zone.

    货舱温度控制区域。
    Cargo hold temperature control zones.
    """

    FROZEN = "frozen"
    """冷冻区(-18C以下) / Frozen (below -18C)."""

    CHILLED = "chilled"
    """冷藏区(0-5C) / Chilled (0-5C)."""

    AMBIENT = "ambient"
    """常温区(15-25C) / Ambient (15-25C)."""

    CONTROLLED = "controlled"
    """受控区(2-8C) / Controlled (2-8C)."""


# 各温度区域的允许温度范围(摄氏度)
_ZONE_RANGES: dict[TempZone, tuple[float, float]] = {
    TempZone.FROZEN: (-40.0, -18.0),
    TempZone.CHILLED: (0.0, 5.0),
    TempZone.AMBIENT: (15.0, 25.0),
    TempZone.CONTROLLED: (2.0, 8.0),
}


@dataclass(frozen=True)
class TemperatureControlConstraint:
    """温控货物约束 / Temperature control constraint.

    校验温控货物要求的温度范围是否在货舱可提供的
    温度区域内，防止货物变质或损坏。
    Validates that the required temperature range of
    temperature-controlled cargo falls within the cargo
    hold's available temperature zone, preventing cargo
    deterioration or damage.

    Attributes:
        cargo_id: 货物标识 / Cargo identifier.
        cargo_min_temp: 货物要求最低温度(C) /
            Cargo required min temperature (C).
        cargo_max_temp: 货物要求最高温度(C) /
            Cargo required max temperature (C).
        cargo_zone: 货物要求的温度区域 / Required temp zone.
        hold_zone: 货舱实际温度区域 / Actual hold temp zone.
    """

    cargo_id: str
    cargo_min_temp: float
    cargo_max_temp: float
    cargo_zone: TempZone
    hold_zone: TempZone

    def check(self) -> AirworthinessResult:
        """执行温控校验 / Perform temperature check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        hold_range = _ZONE_RANGES[self.hold_zone]
        cargo_range = (self.cargo_min_temp, self.cargo_max_temp)

        # 计算温度余量
        margin_low = cargo_range[0] - hold_range[0]
        margin_high = hold_range[1] - cargo_range[1]
        margins[f"temp:{self.cargo_id}:margin_low"] = margin_low
        margins[f"temp:{self.cargo_id}:margin_high"] = margin_high

        # 检查区域匹配
        zone_compatible = self._zones_compatible()
        if not zone_compatible:
            violations.append(
                f"temp_zone_incompatible:"
                f"{self.cargo_id}:"
                f"cargo={self.cargo_zone.value}:"
                f"hold={self.hold_zone.value}"
            )

        # 检查温度范围是否在货舱范围内
        if cargo_range[0] < hold_range[0]:
            violations.append(
                f"temp_too_low:"
                f"{self.cargo_id}:"
                f"cargo_min={self.cargo_min_temp:.1f}:"
                f"hold_min={hold_range[0]:.1f}"
            )

        if cargo_range[1] > hold_range[1]:
            violations.append(
                f"temp_too_high:"
                f"{self.cargo_id}:"
                f"cargo_max={self.cargo_max_temp:.1f}:"
                f"hold_max={hold_range[1]:.1f}"
            )

        # 接近边界时警告
        min_margin = min(margin_low, margin_high)
        if 0 <= min_margin < 3.0:
            return AirworthinessResult.create_warning(
                violations=(
                    f"temp_near_boundary:{self.cargo_id}:min_margin={min_margin:.1f}C",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)

    def _zones_compatible(self) -> bool:
        """检查温度区域兼容性。

        Check temperature zone compatibility.

        Returns:
            若货舱区域可服务货物区域则返回 True。
            True if hold zone can serve cargo zone.
        """
        if self.cargo_zone == self.hold_zone:
            return True
        # 受控区可服务冷藏区
        return bool(
            self.cargo_zone == TempZone.CHILLED
            and self.hold_zone == TempZone.CONTROLLED
        )
