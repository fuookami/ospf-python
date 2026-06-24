"""圆柱体无支撑保护 / Cylinder unsupported guard.

检测圆柱体物品是否缺乏底部支撑。
Detects whether cylindrical items lack bottom support.
"""

from __future__ import annotations

import abc


class CylinderUnsupportedGuard(abc.ABC):
    """圆柱体无支撑保护 / Cylinder unsupported guard.

    验证圆柱体物品放置的稳定性。
    Validates stability of cylindrical item placement.
    """

    @abc.abstractmethod
    def is_supported(
        self,
        item: object,
        position: object,
    ) -> bool:
        """检查支撑状态 / Check support status.

        Args:
            item: 圆柱体物品 / The cylindrical item.
            position: 放置位置 / The placement position.

        Returns:
            有足够支撑返回 True / True if adequately supported.
        """
        ...

    @abc.abstractmethod
    def get_support_ratio(
        self,
        item: object,
        position: object,
    ) -> float:
        """计算支撑比例 / Calculate support ratio.

        Args:
            item: 圆柱体物品 / The cylindrical item.
            position: 放置位置 / The placement position.

        Returns:
            支撑面积比例（0.0-1.0） / Support area ratio
            (0.0-1.0).
        """
        ...
