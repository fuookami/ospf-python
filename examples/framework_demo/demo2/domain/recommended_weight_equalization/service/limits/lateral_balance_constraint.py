"""横向重量平衡约束 / Lateral weight balance constraint.

确保左右两侧舱室的重量保持均衡。
Ensures that the weight of left and right side
compartments remains balanced.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...model.equalization_adjustment import EqualizationAdjustment
from ...model.equalization_result import EqualizationResult


@dataclass(frozen=True)
class LateralCompartmentWeight:
    """横向舱室重量 / Lateral compartment weight.

    描述一个舱室在横向轴上的重量。
    Describes the weight of a compartment on the
    lateral axis.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        weight_kg: 重量 (kg) / Weight (kg).
        side: 所在侧 (left/right) / Side (left/right).
    """

    compartment_id: str
    weight_kg: float
    side: str


@dataclass(frozen=True)
class LateralBalanceConstraint:
    """横向重量平衡约束 / Lateral weight balance constraint.

    校验左右两侧舱室总重量的差值是否在允许范围内，
    超出范围时生成调整建议。
    Validates that the total weight difference between
    left and right side compartments is within the allowed
    range, generating adjustment recommendations when
    exceeded.

    Attributes:
        max_imbalance_ratio: 最大不平衡比例 /
            Maximum imbalance ratio (0.0~1.0).
    """

    max_imbalance_ratio: float = 0.05

    def evaluate(
        self,
        weights: tuple[LateralCompartmentWeight, ...],
    ) -> tuple[bool, EqualizationResult]:
        """评估横向平衡 / Evaluate lateral balance.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            tuple: (是否均衡, 评估结果) /
                (balanced, evaluation result).
        """
        left_total = sum(w.weight_kg for w in weights if w.side == "left")
        right_total = sum(w.weight_kg for w in weights if w.side == "right")
        total = left_total + right_total

        if total == 0.0:
            return (
                True,
                EqualizationResult.create_balanced(
                    max_imbalance=0.0,
                ),
            )

        imbalance = abs(left_total - right_total) / total
        violations: list[str] = []
        adjustments: list[EqualizationAdjustment] = []

        if imbalance > self.max_imbalance_ratio:
            violations.append(
                f"lateral_imbalance:{imbalance:.3f}>{self.max_imbalance_ratio:.3f}"
            )

            target_each = total / 2.0
            for w in weights:
                side_count = sum(1 for x in weights if x.side == w.side)
                target_kg = target_each / max(side_count, 1)
                delta = target_kg - w.weight_kg
                if abs(delta) > 0.01:
                    adjustments.append(
                        EqualizationAdjustment.compute(
                            compartment_id=w.compartment_id,
                            current_kg=w.weight_kg,
                            target_kg=target_kg,
                            axis="lateral",
                        )
                    )

        if violations:
            return (
                False,
                EqualizationResult.create_imbalanced(
                    max_imbalance=imbalance,
                    adjustments=tuple(adjustments),
                    violations=tuple(violations),
                ),
            )

        return (
            True,
            EqualizationResult.create_balanced(
                max_imbalance=imbalance,
                adjustments=tuple(adjustments),
            ),
        )

    def compute_imbalance_ratio(
        self,
        weights: tuple[LateralCompartmentWeight, ...],
    ) -> float:
        """计算横向不平衡比例 / Compute lateral imbalance ratio.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            不平衡比例 (0.0~1.0) / Imbalance ratio (0.0~1.0).
        """
        left = sum(w.weight_kg for w in weights if w.side == "left")
        right = sum(w.weight_kg for w in weights if w.side == "right")
        total = left + right
        if total == 0.0:
            return 0.0
        return abs(left - right) / total

    def side_totals(
        self,
        weights: tuple[LateralCompartmentWeight, ...],
    ) -> dict[str, float]:
        """按侧汇总重量 / Sum weight by side.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            侧标识到总重量的映射。
            Mapping of side to total weight.
        """
        result: dict[str, float] = {"left": 0.0, "right": 0.0}
        for w in weights:
            result[w.side] = result.get(w.side, 0.0) + w.weight_kg
        return result
