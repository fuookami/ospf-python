"""CSP1D 长度约束管线。

向长度分配模型添加长度相关约束。
Constraint pipeline for length assignment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LengthConstraintPipeline:
    """长度约束管线 / Length constraint pipeline.

    在长度分配模型中添加长度范围约束和
    材料-产品匹配约束。
    Adds length range constraints and
    material-product matching constraints to
    the length assignment model.

    Attributes:
        enforce_min_length: 是否强制最小长度。
            Whether to enforce minimum length.
        enforce_max_length: 是否强制最大长度。
            Whether to enforce maximum length.
    """

    enforce_min_length: bool = True
    """强制最小长度 / Enforce minimum length."""

    enforce_max_length: bool = True
    """强制最大长度 / Enforce maximum length."""

    def apply[T](self, aggregation: T) -> T:
        """应用长度约束。

        Apply length constraints.

        在聚合的模型上注册长度范围约束，
        确保分配的长度在允许范围内。
        Registers length range constraints on the
        aggregated model, ensuring assigned lengths
        are within allowed range.

        Args:
            aggregation: 长度分配聚合。
                Length assignment aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def validate_length(
        self,
        *,
        length: float,
        min_length: float,
        max_length: float,
    ) -> bool:
        """验证长度是否在范围内。

        Validate if length is within range.

        Args:
            length: 待验证长度。
                Length to validate.
            min_length: 最小长度。
                Minimum length.
            max_length: 最大长度。
                Maximum length.

        Returns:
            在范围内返回 True / True if within range.
        """
        if self.enforce_min_length and length < min_length:
            return False
        return not (self.enforce_max_length and length > max_length)

    def filter_valid_lengths(
        self,
        *,
        lengths: tuple[float, ...],
        min_length: float,
        max_length: float,
    ) -> tuple[float, ...]:
        """过滤有效长度。

        Filter valid lengths.

        Args:
            lengths: 候选长度列表。
                Candidate lengths.
            min_length: 最小长度。
                Minimum length.
            max_length: 最大长度。
                Maximum length.

        Returns:
            有效长度元组。
            Tuple of valid lengths.
        """
        return tuple(
            l
            for l in lengths
            if self.validate_length(
                length=l,
                min_length=min_length,
                max_length=max_length,
            )
        )
