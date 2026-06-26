"""效能阈值模型。

Effectiveness threshold model for defining score boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectivenessThreshold:
    """装箱效能阈值。

    Defines minimum acceptable and target effectiveness scores
    used to evaluate loading solutions.

    Attributes:
        min_score: 最低可接受得分 (0-1) / Minimum acceptable score (0-1)
        target_score: 目标得分 (0-1) / Target score (0-1)
    """

    min_score: float
    target_score: float

    def __post_init__(self) -> None:
        """验证阈值合理性。

        Validates that thresholds are within valid range and
        target is not below minimum.
        """
        clamped_min = max(0.0, min(self.min_score, 1.0))
        clamped_target = max(clamped_min, min(self.target_score, 1.0))
        object.__setattr__(self, "min_score", clamped_min)
        object.__setattr__(self, "target_score", clamped_target)

    def is_acceptable(self, score: float) -> bool:
        """判断得分是否可接受。

        Args:
            score: 待评估得分 / Score to evaluate

        Returns:
            bool: 是否达到最低标准 / Whether meets minimum standard
        """
        return score >= self.min_score

    def is_target_met(self, score: float) -> bool:
        """判断是否达到目标。

        Args:
            score: 待评估得分 / Score to evaluate

        Returns:
            bool: 是否达到目标 / Whether target is met
        """
        return score >= self.target_score

    def gap_to_target(self, score: float) -> float:
        """计算与目标的差距。

        Args:
            score: 当前得分 / Current score

        Returns:
            float: 差距（正值表示未达标）/ Gap (positive means below target)
        """
        return max(self.target_score - score, 0.0)

    def performance_level(self, score: float) -> str:
        """获取性能等级描述。

        Args:
            score: 当前得分 / Current score

        Returns:
            str: 等级描述 / Performance level description
        """
        if score >= self.target_score:
            return "优秀"
        if score >= self.min_score:
            return "合格"
        return "不合格"
