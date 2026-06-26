"""客舱载荷指数约束 / CLIM constraint.

验证客舱载荷指数是否超过最大允许值。
Validates that the cabin load index does not exceed
the maximum allowable value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.max_clim import MaxCLIM


@dataclass(frozen=True)
class CLIMConstraint:
    """客舱载荷指数约束 / CLIM constraint.

    校验当前甲板在指定飞行阶段的客舱载荷指数
    是否在最大 CLIM 限制之内。
    Validates that the current cabin load index for a deck
    during a specified flight phase is within the max CLIM
    limit.

    Attributes:
        max_clim: 最大CLIM限制 / Max CLIM limit.
        current_load_index: 当前载荷指数 / Current load index.
    """

    max_clim: MaxCLIM
    current_load_index: float

    def check(self) -> AirworthinessResult:
        """执行CLIM校验 / Perform CLIM check.

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        margin = self.max_clim.margin(self.current_load_index)
        margins[
            f"clim:{self.max_clim.deck.value}:{self.max_clim.flight_phase.value}:margin"
        ] = margin

        if not self.max_clim.allows_load_index(self.current_load_index):
            violations.append(
                f"clim_exceeded:"
                f"{self.max_clim.deck.value}:"
                f"{self.max_clim.flight_phase.value}:"
                f"{self.current_load_index:.1f}>"
                f"{self.max_clim.clim_value:.1f}"
            )

        # 起飞关键阶段余量更保守
        warn_pct = 0.05 if self.max_clim.is_takeoff_critical else 0.1
        if 0 <= margin < self.max_clim.clim_value * warn_pct:
            return AirworthinessResult.create_warning(
                violations=(
                    f"clim_near_limit:"
                    f"{self.max_clim.deck.value}:"
                    f"{self.max_clim.flight_phase.value}:"
                    f"margin={margin:.1f}",
                ),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
