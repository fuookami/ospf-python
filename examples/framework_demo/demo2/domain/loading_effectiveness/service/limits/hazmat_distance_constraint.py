"""危险品距离约束。

Hazardous materials distance constraint for safe cargo separation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class HazmatItem:
    """危险品物品信息。

    Item with hazardous material classification.

    Attributes:
        item_id: 物品标识 / Item identifier
        hazmat_class: 危险品分类编号 / Hazmat class number
        position: 物品位置坐标 / Item position (x, y, z)
    """

    item_id: str
    hazmat_class: str
    position: tuple[float, float, float]


@dataclass(frozen=True)
class HazmatDistanceConstraint:
    """危险品最小距离约束。

    Enforces minimum separation distances between incompatible
    hazardous material classes during loading.

    Attributes:
        min_distances: 不兼容类别间的最小距离 / Min distance between incompatible classes
    """

    min_distances: dict[tuple[str, str], float]

    def evaluate(
        self,
        items: tuple[HazmatItem, ...],
    ) -> tuple[bool, list[str]]:
        """评估危险品间距约束。

        Checks all pairs of hazmat items for minimum distance compliance.

        Args:
            items: 危险品物品列表 / List of hazmat items

        Returns:
            tuple: (是否满足, 违规描述) / (satisfied, violation descriptions)
        """
        violations: list[str] = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                required = self._get_min_distance(a.hazmat_class, b.hazmat_class)
                if required is None:
                    continue
                actual = self._euclidean_distance(a.position, b.position)
                if actual < required:
                    violations.append(
                        f"物品 {a.item_id} ({a.hazmat_class}) 与 "
                        f"{b.item_id} ({b.hazmat_class}) 距离 "
                        f"{actual:.2f}m 低于最小要求 {required:.2f}m"
                    )
        return (len(violations) == 0, violations)

    def _get_min_distance(self, class_a: str, class_b: str) -> float | None:
        """获取两类危险品间的最小距离。

        Args:
            class_a: 第一类 / First hazmat class
            class_b: 第二类 / Second hazmat class

        Returns:
            float | None: 最小距离或None（无特殊要求）/ Min distance or None
        """
        key_ab = (class_a, class_b)
        key_ba = (class_b, class_a)
        return self.min_distances.get(key_ab) or self.min_distances.get(key_ba)

    @staticmethod
    def _euclidean_distance(
        a: tuple[float, float, float],
        b: tuple[float, float, float],
    ) -> float:
        """计算欧几里得距离。

        Args:
            a: 坐标点A / Point A
            b: 坐标点B / Point B

        Returns:
            float: 距离 / Euclidean distance
        """
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
