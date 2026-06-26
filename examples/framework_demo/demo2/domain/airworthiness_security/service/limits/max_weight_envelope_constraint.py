"""最大重量包线约束 / Max weight envelope constraint.

验证装箱方案的总重量是否在飞行包线允许范围内。
Validates that the total weight of a packing solution
falls within the flight envelope's allowable range.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult

if TYPE_CHECKING:
    from ...model.envelope import Envelope


@dataclass(frozen=True)
class MaxWeightEnvelopeConstraint:
    """最大重量包线约束 / Max weight envelope constraint.

    校验当前货物总重量是否在指定飞行包线的最小与最大
    重量之间，防止飞机过载或载荷不足。
    Validates that the current total cargo weight lies
    between the minimum and maximum weight of the specified
    flight envelope, preventing overload or insufficient
    loading.

    Attributes:
        envelope: 飞行包线 / Flight envelope.
    """

    envelope: Envelope

    def check(self, total_weight: float) -> AirworthinessResult:
        """执行重量校验 / Perform weight check.

        Args:
            total_weight: 当前总重量(kg)。/ Current total weight (kg).

        Returns:
            校验结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        margin_max = self.envelope.weight_margin(total_weight)
        margins["weight_max_margin"] = margin_max
        margins["weight_min_margin"] = total_weight - self.envelope.min_weight

        if total_weight > self.envelope.max_weight:
            violations.append(
                f"weight_exceeds_max:{total_weight:.1f}>{self.envelope.max_weight:.1f}"
            )

        if total_weight < self.envelope.min_weight:
            violations.append(
                f"weight_below_min:{total_weight:.1f}<{self.envelope.min_weight:.1f}"
            )

        # 接近上限时发出警告(剩余余量 < 5%)
        warn_threshold = self.envelope.weight_range * 0.05
        if 0 <= margin_max < warn_threshold:
            return AirworthinessResult.create_warning(
                violations=(f"weight_near_limit:margin={margin_max:.1f}kg",),
                margins=margins,
            )

        if violations:
            return AirworthinessResult.create_fail(
                violations=tuple(violations),
                margins=margins,
            )

        return AirworthinessResult.create_pass(margins=margins)
