"""重量均衡优化目标 / Weight equalization objective.

最小化舱室间的重量不平衡度。
Minimizes weight imbalance across compartments.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...model.equalization_adjustment import EqualizationAdjustment


@dataclass(frozen=True)
class CompartmentWeight:
    """舱室重量 / Compartment weight.

    用于均衡目标计算的舱室重量数据。
    Compartment weight data for equalization
    objective computation.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        weight_kg: 当前重量 (kg) / Current weight (kg).
        capacity_kg: 最大容量 (kg) / Maximum capacity (kg).
    """

    compartment_id: str
    weight_kg: float
    capacity_kg: float = 0.0


@dataclass(frozen=True)
class EqualizationObjective:
    """重量均衡优化目标 / Weight equalization objective.

    计算所有舱室的重量不平衡度得分，支持横向和纵向
    双轴均衡优化，供优化器最小化。
    Computes the weight imbalance score across all
    compartments, supporting dual-axis (lateral and
    longitudinal) equalization optimization for
    minimization by the optimizer.

    Attributes:
        lateral_weight: 横向均衡权重 /
            Lateral equalization weight.
        longitudinal_weight: 纵向均衡权重 /
            Longitudinal equalization weight.
        target_utilization: 目标利用率 (0.0~1.0) /
            Target utilization ratio (0.0~1.0).
    """

    lateral_weight: float = 0.5
    longitudinal_weight: float = 0.5
    target_utilization: float = 0.85

    def compute(
        self,
        compartments: tuple[CompartmentWeight, ...],
    ) -> tuple[float, float]:
        """计算不平衡度得分。

        Compute imbalance score.

        Args:
            compartments: 各舱室重量 / Compartment weights.

        Returns:
            tuple: (不平衡度, 加权得分) /
                (imbalance, weighted score).
        """
        if not compartments:
            return (0.0, 0.0)

        weights = [c.weight_kg for c in compartments]
        total = sum(weights)
        if total == 0.0:
            return (0.0, 0.0)

        avg = total / len(weights)
        deviations = [abs(w - avg) for w in weights]
        max_dev = max(deviations) if deviations else 0.0
        imbalance = max_dev / total if total > 0.0 else 0.0

        score = imbalance * (self.lateral_weight + self.longitudinal_weight)
        return (imbalance, score)

    def generate_adjustments(
        self,
        compartments: tuple[CompartmentWeight, ...],
    ) -> tuple[EqualizationAdjustment, ...]:
        """生成均衡调整建议 / Generate equalization adjustments.

        Args:
            compartments: 各舱室重量 / Compartment weights.

        Returns:
            调整建议元组 / Tuple of adjustment recommendations.
        """
        if not compartments:
            return ()

        total = sum(c.weight_kg for c in compartments)
        avg = total / len(compartments)
        adjustments: list[EqualizationAdjustment] = []

        for c in compartments:
            delta = avg - c.weight_kg
            if abs(delta) > 0.01:
                adjustments.append(
                    EqualizationAdjustment.compute(
                        compartment_id=c.compartment_id,
                        current_kg=c.weight_kg,
                        target_kg=avg,
                        axis="lateral",
                    )
                )

        return tuple(adjustments)

    def utilization_gaps(
        self,
        compartments: tuple[CompartmentWeight, ...],
    ) -> dict[str, float]:
        """计算各舱室与目标利用率的差距。

        Compute per-compartment gap to target utilization.

        Args:
            compartments: 各舱室重量 / Compartment weights.

        Returns:
            舱室标识到差距的映射（正数表示未达标）。
            Mapping of compartment ID to gap (positive = below).
        """
        result: dict[str, float] = {}
        for c in compartments:
            if c.capacity_kg <= 0.0:
                result[c.compartment_id] = 0.0
                continue
            current_ratio = c.weight_kg / c.capacity_kg
            gap = self.target_utilization - current_ratio
            result[c.compartment_id] = max(0.0, gap)
        return result

    def imbalance_ranking(
        self,
        compartments: tuple[CompartmentWeight, ...],
    ) -> tuple[CompartmentWeight, ...]:
        """按不平衡程度排序 / Rank by imbalance degree.

        Args:
            compartments: 各舱室重量 / Compartment weights.

        Returns:
            按与平均值偏差降序排列的舱室。
            Compartments sorted by deviation from mean descending.
        """
        if not compartments:
            return ()
        total = sum(c.weight_kg for c in compartments)
        avg = total / len(compartments)
        return tuple(
            sorted(
                compartments,
                key=lambda c: abs(c.weight_kg - avg),
                reverse=True,
            )
        )
