"""快递优先级枚举。

Express priority enum for delivery speed classification.
"""

from __future__ import annotations

from enum import IntEnum


class ExpressPriority(IntEnum):
    """快递优先级。

    Express delivery priority levels determining the speed
    and handling requirements for shipments.

    Attributes:
        SAME_DAY: 当日达 / Same-day delivery (highest)
        NEXT_DAY: 次日达 / Next-day delivery
        STANDARD: 标准快递 / Standard delivery (lowest)
    """

    SAME_DAY = 1
    NEXT_DAY = 2
    STANDARD = 3

    def label_zh(self) -> str:
        """获取中文标签。

        Returns:
            str: 中文标签 / Chinese label
        """
        mapping = {
            ExpressPriority.SAME_DAY: "当日达",
            ExpressPriority.NEXT_DAY: "次日达",
            ExpressPriority.STANDARD: "标准快递",
        }
        return mapping[self]

    def label_en(self) -> str:
        """获取英文标签。

        Returns:
            str: 英文标签 / English label
        """
        return self.name

    def max_hours(self) -> float:
        """获取最大配送时限（小时）。

        Returns:
            float: 最大配送时间 / Maximum delivery time in hours
        """
        mapping = {
            ExpressPriority.SAME_DAY: 8.0,
            ExpressPriority.NEXT_DAY: 24.0,
            ExpressPriority.STANDARD: 72.0,
        }
        return mapping[self]

    def cost_multiplier(self) -> float:
        """获取成本倍率。

        Returns:
            float: 成本倍率 / Cost multiplier relative to standard
        """
        mapping = {
            ExpressPriority.SAME_DAY: 3.0,
            ExpressPriority.NEXT_DAY: 2.0,
            ExpressPriority.STANDARD: 1.0,
        }
        return mapping[self]

    def is_higher_than(self, other: ExpressPriority) -> bool:
        """判断是否比另一优先级更高。

        Args:
            other: 另一优先级 / Other priority

        Returns:
            bool: 是否更高 / Whether higher priority
        """
        return self.value < other.value
