"""载荷最大化结果 / Payload maximization result.

定义载荷最大化计算的结果数据结构。
Defines the result data structure for payload maximization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayloadResult:
    """载荷最大化结果 / Payload maximization result.

    汇总载荷最大化分析的最大可用载荷、限制因素和可行性，
    供上层应用决策使用。
    Summarizes the maximum usable payload, limiting factor,
    and feasibility of payload maximization analysis for
    upper-layer application decision-making.

    Attributes:
        max_payload: 最大可用载荷(kg) /
            Maximum usable payload (kg).
        limiting_factor: 限制因素描述 /
            Limiting factor description.
        feasible: 方案是否可行 /
            Whether the solution is feasible.
        weight_margin: 重量余量(kg) / Weight margin (kg).
        envelope_margin: 包线余量(kg) / Envelope margin (kg).
    """

    max_payload: float
    limiting_factor: str
    feasible: bool
    weight_margin: float = 0.0
    envelope_margin: float = 0.0

    @staticmethod
    def create_feasible(
        *,
        max_payload: float,
        weight_margin: float = 0.0,
        envelope_margin: float = 0.0,
    ) -> PayloadResult:
        """创建可行结果 / Create feasible result.

        Args:
            max_payload: 最大载荷(kg) / Max payload (kg).
            weight_margin: 重量余量(kg) / Weight margin (kg).
            envelope_margin: 包线余量(kg) / Envelope margin (kg).

        Returns:
            可行的载荷结果 / Feasible payload result.
        """
        limiting = "none"
        limiting = "weight" if weight_margin <= envelope_margin else "envelope"
        return PayloadResult(
            max_payload=max_payload,
            limiting_factor=limiting,
            feasible=True,
            weight_margin=weight_margin,
            envelope_margin=envelope_margin,
        )

    @staticmethod
    def create_infeasible(
        *,
        limiting_factor: str,
    ) -> PayloadResult:
        """创建不可行结果 / Create infeasible result.

        Args:
            limiting_factor: 限制因素 / Limiting factor.

        Returns:
            不可行的载荷结果 / Infeasible payload result.
        """
        return PayloadResult(
            max_payload=0.0,
            limiting_factor=limiting_factor,
            feasible=False,
            weight_margin=0.0,
            envelope_margin=0.0,
        )

    @property
    def is_weight_limited(self) -> bool:
        """是否受重量限制 / Is weight limited.

        Returns:
            限制因素为重量时返回 True。
            True if limiting factor is weight.
        """
        return self.limiting_factor == "weight"

    @property
    def is_envelope_limited(self) -> bool:
        """是否受包线限制 / Is envelope limited.

        Returns:
            限制因素为包线时返回 True。
            True if limiting factor is envelope.
        """
        return self.limiting_factor == "envelope"

    @property
    def critical_margin(self) -> float:
        """关键余量 / Critical margin.

        Returns:
            取重量余量和包线余量的较小值。
            Minimum of weight margin and envelope margin.
        """
        return min(self.weight_margin, self.envelope_margin)

    def can_add_weight(self, additional_kg: float) -> bool:
        """检查是否可额外增加重量。

        Check whether additional weight can be added.

        Args:
            additional_kg: 额外重量(kg) / Additional weight (kg).

        Returns:
            若关键余量足够则返回 True。
            True if critical margin is sufficient.
        """
        if not self.feasible:
            return False
        return additional_kg <= self.critical_margin
