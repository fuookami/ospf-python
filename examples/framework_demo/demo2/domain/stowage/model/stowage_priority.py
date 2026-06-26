"""装载优先级 / Stowage priority.

定义货物装载的优先级等级。
Defines priority levels for cargo loading.
"""

from __future__ import annotations

import enum


class StowagePriority(enum.IntEnum):
    """装载优先级 / Stowage priority.

    表示货物装载的优先级，数值越小优先级越高。
    Represents cargo loading priority; lower values indicate
    higher priority.

    Attributes:
        CRITICAL: 关键优先级，必须首先装载 /
            Critical priority, must be loaded first.
        HIGH: 高优先级 / High priority.
        MEDIUM: 中等优先级 / Medium priority.
        LOW: 低优先级，最后装载 /
            Low priority, loaded last.
    """

    CRITICAL = 0
    """关键优先级 / Critical priority."""

    HIGH = 1
    """高优先级 / High priority."""

    MEDIUM = 2
    """中等优先级 / Medium priority."""

    LOW = 3
    """低优先级 / Low priority."""

    @staticmethod
    def from_weight(weight: float) -> StowagePriority:
        """根据权重推断优先级。

        Infer priority from weight value.

        Args:
            weight: 权重值（0.0-1.0）。/ Weight value (0.0-1.0).

        Returns:
            对应的优先级。/ Corresponding priority.
        """
        if weight >= 0.9:
            return StowagePriority.CRITICAL
        if weight >= 0.6:
            return StowagePriority.HIGH
        if weight >= 0.3:
            return StowagePriority.MEDIUM
        return StowagePriority.LOW

    @property
    def weight(self) -> float:
        """优先级权重。

        Priority weight.

        Returns:
            0.0（最高）到 1.0（最低）的权重值。
            Weight value from 0.0 (highest) to 1.0 (lowest).
        """
        return self.value / 3.0

    def dominates(self, other: StowagePriority) -> bool:
        """判断是否优先于另一优先级。

        Check whether this priority dominates another.

        Args:
            other: 另一优先级。/ The other priority.

        Returns:
            若本优先级更高则返回 True。
            True if this priority is higher.
        """
        return self.value < other.value
