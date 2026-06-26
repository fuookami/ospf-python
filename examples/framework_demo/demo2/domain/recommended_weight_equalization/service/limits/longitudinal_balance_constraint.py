"""纵向重量平衡约束 / Longitudinal weight balance constraint.

确保前后舱室的重量保持均衡，维护重心在安全范围内。
Ensures that front and rear compartment weights remain
balanced, keeping the center of gravity within safe range.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...model.equalization_adjustment import EqualizationAdjustment
from ...model.equalization_result import EqualizationResult


@dataclass(frozen=True)
class LongitudinalCompartmentWeight:
    """纵向舱室重量 / Longitudinal compartment weight.

    描述一个舱室在纵轴上的重量和位置。
    Describes the weight and position of a compartment
    on the longitudinal axis.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        weight_kg: 重量 (kg) / Weight (kg).
        station_m: 纵向站位 (m，机头为正) /
            Longitudinal station (m, nose positive).
        zone: 区域 (front/center/rear) /
            Zone (front/center/rear).
    """

    compartment_id: str
    weight_kg: float
    station_m: float = 0.0
    zone: str = "center"


@dataclass(frozen=True)
class LongitudinalBalanceConstraint:
    """纵向重量平衡约束 / Longitudinal weight balance constraint.

    校验前后区域舱室的重量差是否在允许范围内，
    并验证合成重心站位是否处于安全区间。
    Validates that the weight difference between front
    and rear zones is within the allowed range and that
    the resulting center-of-gravity station is within
    the safe interval.

    Attributes:
        max_imbalance_ratio: 最大不平衡比例 /
            Maximum imbalance ratio (0.0~1.0).
        cg_forward_limit_m: 重心前限 (m) /
            CG forward limit (m).
        cg_aft_limit_m: 重心后限 (m) /
            CG aft limit (m).
    """

    max_imbalance_ratio: float = 0.08
    cg_forward_limit_m: float = 20.0
    cg_aft_limit_m: float = 30.0

    def evaluate(
        self,
        weights: tuple[LongitudinalCompartmentWeight, ...],
    ) -> tuple[bool, EqualizationResult]:
        """评估纵向平衡 / Evaluate longitudinal balance.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            tuple: (是否均衡, 评估结果) /
                (balanced, evaluation result).
        """
        front_total = sum(w.weight_kg for w in weights if w.zone == "front")
        rear_total = sum(w.weight_kg for w in weights if w.zone == "rear")
        total = sum(w.weight_kg for w in weights)

        violations: list[str] = []
        adjustments: list[EqualizationAdjustment] = []

        if total == 0.0:
            return (
                True,
                EqualizationResult.create_balanced(
                    max_imbalance=0.0,
                ),
            )

        imbalance = abs(front_total - rear_total) / total
        if imbalance > self.max_imbalance_ratio:
            violations.append(
                f"longitudinal_imbalance:{imbalance:.3f}>{self.max_imbalance_ratio:.3f}"
            )

        moment = sum(w.weight_kg * w.station_m for w in weights)
        cg_station = moment / total
        if cg_station < self.cg_forward_limit_m:
            violations.append(
                f"cg_forward_exceeded:{cg_station:.2f}m<{self.cg_forward_limit_m:.2f}m"
            )
        elif cg_station > self.cg_aft_limit_m:
            violations.append(
                f"cg_aft_exceeded:{cg_station:.2f}m>{self.cg_aft_limit_m:.2f}m"
            )

        if violations:
            adjustments = self._compute_adjustments(
                weights,
                front_total,
                rear_total,
                total,
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

    def _compute_adjustments(
        self,
        weights: tuple[LongitudinalCompartmentWeight, ...],
        front_total: float,
        rear_total: float,
        total: float,
    ) -> list[EqualizationAdjustment]:
        """计算调整建议 / Compute adjustment recommendations.

        Args:
            weights: 各舱室重量 / Compartment weights.
            front_total: 前区总重 / Front zone total.
            rear_total: 后区总重 / Rear zone total.
            total: 总重 / Grand total.

        Returns:
            调整明细列表 / List of adjustments.
        """
        target_each = total / 2.0
        adjustments: list[EqualizationAdjustment] = []
        for w in weights:
            if w.zone == "front" or w.zone == "rear":
                pass
            else:
                continue

            zone_count = sum(1 for x in weights if x.zone == w.zone)
            target_kg = target_each / max(zone_count, 1)
            delta = target_kg - w.weight_kg
            if abs(delta) > 0.01:
                adjustments.append(
                    EqualizationAdjustment.compute(
                        compartment_id=w.compartment_id,
                        current_kg=w.weight_kg,
                        target_kg=target_kg,
                        axis="longitudinal",
                    )
                )
        return adjustments

    def compute_cg_station(
        self,
        weights: tuple[LongitudinalCompartmentWeight, ...],
    ) -> float:
        """计算合成重心站位 / Compute resulting CG station.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            重心站位 (m)，无重量时返回 0.0。
            CG station (m); 0.0 if no weight.
        """
        total = sum(w.weight_kg for w in weights)
        if total == 0.0:
            return 0.0
        return sum(w.weight_kg * w.station_m for w in weights) / total

    def zone_totals(
        self,
        weights: tuple[LongitudinalCompartmentWeight, ...],
    ) -> dict[str, float]:
        """按区域汇总重量 / Sum weight by zone.

        Args:
            weights: 各舱室重量 / Compartment weights.

        Returns:
            区域标识到总重量的映射。
            Mapping of zone to total weight.
        """
        result: dict[str, float] = {
            "front": 0.0,
            "center": 0.0,
            "rear": 0.0,
        }
        for w in weights:
            result[w.zone] = result.get(w.zone, 0.0) + w.weight_kg
        return result
