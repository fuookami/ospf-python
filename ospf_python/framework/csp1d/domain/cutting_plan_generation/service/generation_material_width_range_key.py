"""CSP1D 材料宽度范围键。

用于按宽度范围分组材料的值对象。
Value object for grouping materials by width range.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationMaterialWidthRangeKey:
    """材料宽度范围键 / Material width range key.

    作为字典键使用，将材料按宽度范围分组，
    使相同宽度范围的材料共享生成结果。
    Used as a dictionary key to group materials by
    width range, sharing generation results among
    materials with the same width range.

    Attributes:
        min_width: 范围最小宽度。
            Range minimum width.
        max_width: 范围最大宽度。
            Range maximum width.
        precision: 数值比较精度。
            Numerical comparison precision.
    """

    min_width: float = 0.0
    """范围最小宽度 / Range minimum width."""

    max_width: float = 0.0
    """范围最大宽度 / Range maximum width."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""

    def contains(self, width: float) -> bool:
        """检查宽度是否在范围内。

        Check if width is within range.

        Args:
            width: 待检查的宽度。
                Width to check.

        Returns:
            在范围内返回 True / True if within range.
        """
        return (
            self.min_width - self.precision
            <= width
            <= self.max_width + self.precision
        )

    @property
    def range_span(self) -> float:
        """获取宽度范围跨度。

        Get width range span.

        Returns:
            最大宽度与最小宽度之差。
            Difference between max and min width.
        """
        return self.max_width - self.min_width

    @property
    def is_valid(self) -> bool:
        """验证键是否有效。

        Validate if key is valid.

        Returns:
            最小宽度非负且不大于最大宽度时返回 True。
            True when min width is non-negative and not greater than max.
        """
        return self.min_width >= 0.0 and self.min_width <= self.max_width

    def overlaps(self, other: GenerationMaterialWidthRangeKey) -> bool:
        """检查是否与另一范围重叠。

        Check if overlaps with another range.

        Args:
            other: 另一宽度范围键。
                Another width range key.

        Returns:
            重叠返回 True / True if overlapping.
        """
        return (
            self.min_width <= other.max_width + self.precision
            and other.min_width <= self.max_width + self.precision
        )

    @staticmethod
    def from_width(
        width: float,
        tolerance: float = 0.0,
    ) -> GenerationMaterialWidthRangeKey:
        """从单一宽度创建范围键。

        Create range key from a single width.

        Args:
            width: 材料宽度。
                Material width.
            tolerance: 容差范围，默认 0.0。
                Tolerance range, default 0.0.

        Returns:
            宽度范围键实例。
            Width range key instance.
        """
        return GenerationMaterialWidthRangeKey(
            min_width=max(0.0, width - tolerance),
            max_width=width + tolerance,
        )
