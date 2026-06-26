"""重心包线约束 / CG envelope constraint.

验证装箱方案的重心位置是否在飞行包线允许范围内。
Validates that the CG position of a packing solution
falls within the flight envelope's allowable range.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.envelope import Envelope


@dataclass(frozen=True)
class CGEnvelopeConstraint:
    """重心包线约束 / CG envelope constraint.

    校验当前货物重心位置(以 %MAC 计)是否在指定飞行
    包线的最小与最大重心之间，保证飞行稳定性。
    Validates that the current cargo CG position (in %MAC)
    lies between the min and max CG of the specified flight
    envelope, ensuring flight stability.

    Attributes:
        envelope: 飞行包线 / Flight envelope.
    """

    envelope: Envelope

    def check(self, cg_position: float) -> AirworthinessResult:
        """执行重心校验 / Perform CG check.

        Args:
            cg_position: 当前重心位置(%MAC)。/ Current CG (%MAC).

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        margin = self.envelope.cg_margin(cg_position)
        margins["cg_margin"] = margin
        margins["cg_to_min"] = cg_position - self.envelope.min_cg
        margins["cg_to_max"] = self.envelope.max_cg - cg_position

        if cg_position > self.envelope.max_cg:
            violations.append(
                f"cg_exceeds_max:{cg_position:.2f}%>{self.envelope.max_cg:.2f}%"
            )

        if cg_position < self.envelope.min_cg:
            violations.append(
                f"cg_below_min:{cg_position:.2f}%<{self.envelope.min_cg:.2f}%"
            )

        # 接近边界时发出警告
        warn_threshold = self.envelope.cg_range * 0.1
        if 0 <= margin < warn_threshold:
            return AirworthinessResult.create_warning(
                violations=(f"cg_near_boundary:margin={margin:.2f}%MAC",),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
