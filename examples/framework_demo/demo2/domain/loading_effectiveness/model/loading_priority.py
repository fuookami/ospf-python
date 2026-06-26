"""装载优先级枚举。

Loading priority enum for item classification.
"""

from __future__ import annotations

from enum import IntEnum


class LoadingPriority(IntEnum):
    """装载优先级。

    Loading priority levels controlling the order and importance
    of items during the loading process.

    Attributes:
        CRITICAL: 关键优先级 / Critical priority (highest)
        HIGH: 高优先级 / High priority
        MEDIUM: 中优先级 / Medium priority
        LOW: 低优先级 / Low priority (lowest)
    """

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def label_zh(self) -> str:
        """获取中文标签。

        Returns:
            str: 中文优先级标签 / Chinese priority label
        """
        mapping = {
            LoadingPriority.CRITICAL: "关键",
            LoadingPriority.HIGH: "高",
            LoadingPriority.MEDIUM: "中",
            LoadingPriority.LOW: "低",
        }
        return mapping[self]

    def label_en(self) -> str:
        """获取英文标签。

        Returns:
            str: 英文优先级标签 / English priority label
        """
        return self.name

    def is_higher_than(self, other: LoadingPriority) -> bool:
        """判断是否比另一优先级更高。

        Args:
            other: 另一优先级 / Other priority to compare

        Returns:
            bool: 是否更高 / Whether this is higher priority
        """
        return self.value < other.value
