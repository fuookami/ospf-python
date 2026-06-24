"""归一化 / Normalization.

提供目标函数值的归一化功能。
Provides objective value normalization functionality.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Normalization:
    """归一化 / Normalization.

    将目标函数值归一化到指定范围。
    Normalizes objective values to a specified range.

    Attributes:
        min_val: 归一化范围下界 / Normalization lower bound.
        max_val: 归一化范围上界 / Normalization upper bound.
    """

    min_val: float = 0.0
    """归一化范围下界 / Normalization lower bound."""

    max_val: float = 1.0
    """归一化范围上界 / Normalization upper bound."""

    def normalize(
        self,
        value: float,
        *,
        source_min: float,
        source_max: float,
    ) -> float:
        """归一化单个值 / Normalize a single value.

        Args:
            value: 输入值 / Input value.
            source_min: 源范围下界 / Source lower bound.
            source_max: 源范围上界 / Source upper bound.

        Returns:
            归一化后的值 / Normalized value.
        """
        span = source_max - source_min
        if abs(span) < 1e-12:
            return self.min_val
        ratio = (value - source_min) / span
        return self.min_val + ratio * (self.max_val - self.min_val)

    def normalize_batch(
        self,
        values: list[float],
    ) -> list[float]:
        """批量归一化 / Batch normalization.

        Args:
            values: 输入值列表 / List of input values.

        Returns:
            归一化后的值列表 / List of normalized values.
        """
        if not values:
            return []
        lo = min(values)
        hi = max(values)
        return [
            self.normalize(
                v,
                source_min=lo,
                source_max=hi,
            )
            for v in values
        ]
