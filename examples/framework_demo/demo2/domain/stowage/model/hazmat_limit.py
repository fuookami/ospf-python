"""危险品限制 / Hazmat limit.

定义危险品货物的隔离距离要求。
Defines segregation distance requirements for hazardous cargo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HazmatLimit:
    """危险品限制 / Hazmat limit.

    描述危险品货物的隔离等级和最小隔离距离，
    确保不同危险等级的货物保持安全间隔。
    Describes the segregation class and minimum segregation
    distance for hazardous cargo, ensuring safe separation
    between different hazard levels.

    Attributes:
        item_id: 货物标识 / Item identifier.
        hazard_class: 危险等级（1-9）/
            Hazard class (1-9).
        segregation_distance: 最小隔离距离（米）/
            Minimum segregation distance (m).
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    hazard_class: int = 0
    """危险等级（1-9）/ Hazard class (1-9)."""

    segregation_distance: float = 0.0
    """最小隔离距离（米）/ Minimum segregation distance (m)."""

    @staticmethod
    def create(
        *,
        item_id: str,
        hazard_class: int,
        segregation_distance: float,
    ) -> HazmatLimit:
        """创建危险品限制。

        Create hazmat limit.

        Args:
            item_id: 货物标识。/ Item identifier.
            hazard_class: 危险等级（1-9）。/ Hazard class (1-9).
            segregation_distance: 最小隔离距离（米）。/
                Minimum segregation distance (m).

        Returns:
            限制实例。/ Limit instance.
        """
        clamped_class = max(1, min(9, hazard_class))
        return HazmatLimit(
            item_id=item_id,
            hazard_class=clamped_class,
            segregation_distance=max(0.0, segregation_distance),
        )

    @property
    def is_explosive(self) -> bool:
        """是否为爆炸品。

        Whether the item is explosive.

        Returns:
            危险等级为 1 时返回 True。
            True if hazard class is 1.
        """
        return self.hazard_class == 1

    @property
    def is_flammable(self) -> bool:
        """是否为易燃品。

        Whether the item is flammable.

        Returns:
            危险等级为 3 时返回 True。
            True if hazard class is 3.
        """
        return self.hazard_class == 3

    @property
    def is_toxic(self) -> bool:
        """是否为有毒品。

        Whether the item is toxic.

        Returns:
            危险等级为 6 时返回 True。
            True if hazard class is 6.
        """
        return self.hazard_class == 6

    @property
    def is_radioactive(self) -> bool:
        """是否为放射性物品。

        Whether the item is radioactive.

        Returns:
            危险等级为 7 时返回 True。
            True if hazard class is 7.
        """
        return self.hazard_class == 7

    def required_segregation_distance(
        self,
        other_class: int,
    ) -> float:
        """计算与另一危险等级的所需隔离距离。

        Calculate required segregation distance from another
        hazard class.

        Args:
            other_class: 另一危险等级。/ Other hazard class.

        Returns:
            所需隔离距离（米），取两者较大值。
            Required segregation distance (m), taking the larger value.
        """
        base_distance = self.segregation_distance
        class_factor = max(self.hazard_class, other_class) / 9.0
        return base_distance * (1.0 + class_factor)

    def can_coexist(
        self,
        other_class: int,
        distance: float,
    ) -> bool:
        """检查是否可以与另一危险品共存。

        Check whether it can coexist with another hazmat item.

        Args:
            other_class: 另一危险等级。/ Other hazard class.
            distance: 实际距离（米）。/ Actual distance (m).

        Returns:
            距离满足隔离要求时返回 True。
            True if distance meets segregation requirement.
        """
        required = self.required_segregation_distance(other_class)
        return distance >= required
