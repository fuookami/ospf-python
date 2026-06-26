"""重量均衡结果 / Weight equalization result.

定义重量均衡调整的结果数据结构。
Defines the result data structure for weight
equalization adjustments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .equalization_adjustment import EqualizationAdjustment


@dataclass(frozen=True)
class EqualizationResult:
    """重量均衡结果 / Weight equalization result.

    汇总重量均衡调整的状态、最大不平衡度和调整明细，
    供上层应用决策使用。
    Summarizes the equalization status, maximum imbalance,
    and adjustment details for upper-layer application
    decision-making.

    Attributes:
        status: 均衡状态描述 / Equalization status label.
        max_imbalance: 最大不平衡度 (0.0~1.0) /
            Maximum imbalance ratio (0.0~1.0).
        adjustments: 调整明细元组 /
            Tuple of adjustment details.
        violations: 违规描述元组 /
            Tuple of violation descriptions.
    """

    status: str
    max_imbalance: float
    adjustments: tuple[EqualizationAdjustment, ...] = ()
    violations: tuple[str, ...] = ()

    @staticmethod
    def create_balanced(
        *,
        max_imbalance: float,
        adjustments: tuple[EqualizationAdjustment, ...] = (),
    ) -> EqualizationResult:
        """创建均衡结果 / Create balanced result.

        Args:
            max_imbalance: 最大不平衡度 / Maximum imbalance.
            adjustments: 调整明细 / Adjustment details.

        Returns:
            均衡状态的结果 / Balanced result.
        """
        return EqualizationResult(
            status="balanced",
            max_imbalance=max_imbalance,
            adjustments=adjustments,
            violations=(),
        )

    @staticmethod
    def create_imbalanced(
        *,
        max_imbalance: float,
        adjustments: tuple[EqualizationAdjustment, ...] = (),
        violations: tuple[str, ...] = (),
    ) -> EqualizationResult:
        """创建不均衡结果 / Create imbalanced result.

        Args:
            max_imbalance: 最大不平衡度 / Maximum imbalance.
            adjustments: 调整明细 / Adjustment details.
            violations: 违规描述 / Violations.

        Returns:
            不均衡状态的结果 / Imbalanced result.
        """
        return EqualizationResult(
            status="imbalanced",
            max_imbalance=max_imbalance,
            adjustments=adjustments,
            violations=violations,
        )

    @property
    def is_balanced(self) -> bool:
        """是否均衡 / Is balanced.

        Returns:
            状态为 "balanced" 时返回 True。
            True if status is "balanced".
        """
        return self.status == "balanced"

    @property
    def adjustment_count(self) -> int:
        """调整数量 / Adjustment count."""
        return len(self.adjustments)

    @property
    def violation_count(self) -> int:
        """违规数量 / Violation count."""
        return len(self.violations)

    @property
    def total_delta(self) -> float:
        """总调整量 / Total adjustment delta.

        Returns:
            所有调整的绝对值之和。
            Sum of absolute deltas across all adjustments.
        """
        return sum(abs(a.delta_kg) for a in self.adjustments)

    def merge(
        self,
        other: EqualizationResult,
    ) -> EqualizationResult:
        """合并两个结果 / Merge two results.

        取较大不平衡度；任一不均衡则不均衡；合并调整和违规。

        Args:
            other: 另一个结果 / Another result.

        Returns:
            合并后的新结果 / New merged result.
        """
        merged_adj = self.adjustments + other.adjustments
        merged_violations = self.violations + other.violations
        is_balanced = self.is_balanced and other.is_balanced
        status = "balanced" if is_balanced else "imbalanced"
        return EqualizationResult(
            status=status,
            max_imbalance=max(
                self.max_imbalance,
                other.max_imbalance,
            ),
            adjustments=merged_adj,
            violations=merged_violations,
        )
