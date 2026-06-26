"""重量均衡上下文 / Weight equalization context.

管理重量均衡评估的注册与验证流程。
Manages registration and validation for weight
equalization evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .equalization_aggregation import EqualizationAggregation
from .equalization_result import EqualizationResult

if TYPE_CHECKING:
    from .equalization_adjustment import EqualizationAdjustment


@dataclass
class EqualizationContext:
    """重量均衡上下文 / Weight equalization context.

    提供可变的注册接口，收集舱室调整和评估结果后可生成
    不可变的聚合对象并执行均衡验证。
    Provides a mutable registration interface; after
    collecting compartment adjustments and evaluation results,
    generates an immutable aggregation object and performs
    balance validation.

    Attributes:
        _adjustments: 已注册调整 / Registered adjustments.
        _results: 已注册结果 / Registered results.
        _max_tolerance: 最大容忍不平衡度 /
            Maximum tolerated imbalance.
    """

    _adjustments: list[EqualizationAdjustment] = field(
        default_factory=list,
        init=False,
    )
    _results: list[EqualizationResult] = field(
        default_factory=list,
        init=False,
    )
    _max_tolerance: float = field(
        default=0.05,
        init=False,
    )

    def register_adjustment(
        self,
        adjustment: EqualizationAdjustment,
    ) -> None:
        """注册舱室调整 / Register compartment adjustment.

        Args:
            adjustment: 调整明细 / Adjustment detail.
        """
        self._adjustments.append(adjustment)

    def register_result(
        self,
        result: EqualizationResult,
    ) -> None:
        """注册评估结果 / Register evaluation result.

        Args:
            result: 评估结果 / Evaluation result.
        """
        self._results.append(result)

    def set_max_tolerance(self, tolerance: float) -> None:
        """设置最大容忍不平衡度 / Set max tolerance.

        Args:
            tolerance: 不平衡度阈值 / Imbalance threshold.
        """
        self._max_tolerance = min(1.0, max(0.0, tolerance))

    @property
    def max_tolerance(self) -> float:
        """最大容忍不平衡度 / Maximum tolerance."""
        return self._max_tolerance

    @property
    def adjustment_count(self) -> int:
        """已注册调整数 / Registered adjustment count."""
        return len(self._adjustments)

    @property
    def result_count(self) -> int:
        """已注册结果数 / Registered result count."""
        return len(self._results)

    def find_adjustment(
        self,
        compartment_id: str,
    ) -> EqualizationAdjustment | None:
        """按标识查找调整 / Find adjustment by compartment ID.

        Args:
            compartment_id: 舱室标识 / Compartment identifier.

        Returns:
            匹配的调整或 None。
            Matching adjustment, or None.
        """
        for a in self._adjustments:
            if a.compartment_id == compartment_id:
                return a
        return None

    def lateral_adjustments(
        self,
    ) -> tuple[EqualizationAdjustment, ...]:
        """获取横向调整 / Get lateral adjustments.

        Returns:
            轴向为 lateral 的调整元组。
            Tuple of lateral adjustments.
        """
        return tuple(a for a in self._adjustments if a.is_lateral)

    def longitudinal_adjustments(
        self,
    ) -> tuple[EqualizationAdjustment, ...]:
        """获取纵向调整 / Get longitudinal adjustments.

        Returns:
            轴向为 longitudinal 的调整元组。
            Tuple of longitudinal adjustments.
        """
        return tuple(a for a in self._adjustments if a.is_longitudinal)

    def build_aggregation(self) -> EqualizationAggregation:
        """构建不可变聚合对象 / Build immutable aggregation.

        Returns:
            包含所有已注册结果的聚合对象。
            Aggregation with all registered results.
        """
        return EqualizationAggregation(
            results=tuple(self._results),
        )

    def validate(self) -> EqualizationResult:
        """执行均衡验证 / Perform balance validation.

        检查已注册调整是否在容忍范围内。
        Checks whether registered adjustments are
        within tolerance.

        Returns:
            验证结果 / Validation result.
        """
        violations: list[str] = []

        for adj in self._adjustments:
            if adj.absolute_delta > 0.0:
                pct = abs(adj.percentage_change)
                if pct > self._max_tolerance * 100.0:
                    violations.append(
                        f"excessive_adjustment:"
                        f"{adj.compartment_id}:"
                        f"{pct:.1f}%>"
                        f"{self._max_tolerance * 100.0:.1f}%"
                    )

        lateral = self.lateral_adjustments()
        if lateral:
            left_delta = sum(a.delta_kg for a in lateral if a.delta_kg > 0)
            right_delta = sum(abs(a.delta_kg) for a in lateral if a.delta_kg < 0)
            total = left_delta + right_delta
            if total > 0.0:
                imbalance = abs(left_delta - right_delta) / total
                if imbalance > self._max_tolerance:
                    violations.append(
                        f"lateral_imbalance:{imbalance:.3f}>{self._max_tolerance:.3f}"
                    )

        max_imb = max(
            (abs(a.percentage_change) / 100.0 for a in self._adjustments),
            default=0.0,
        )

        if violations:
            return EqualizationResult.create_imbalanced(
                max_imbalance=max_imb,
                adjustments=tuple(self._adjustments),
                violations=tuple(violations),
            )

        return EqualizationResult.create_balanced(
            max_imbalance=max_imb,
            adjustments=tuple(self._adjustments),
        )
