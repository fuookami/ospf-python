"""温区隔离约束。

Temperature zone segregation constraint for cargo compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureItem:
    """温控物品信息。

    Item with temperature requirements.

    Attributes:
        item_id: 物品标识 / Item identifier
        temp_min: 最低温度要求 / Minimum temperature requirement (°C)
        temp_max: 最高温度要求 / Maximum temperature requirement (°C)
        compartment_id: 分配舱室 / Assigned compartment
    """

    item_id: str
    temp_min: float
    temp_max: float
    compartment_id: str


@dataclass(frozen=True)
class TemperatureZoneConstraint:
    """温区隔离约束。

    Enforces that items sharing the same compartment have compatible
    temperature requirements. Items with non-overlapping temperature
    ranges cannot be placed in the same compartment.

    Attributes:
        compartment_temps: 各舱室温度设定 / Compartment temperature settings (°C)
        tolerance: 温度容差 / Temperature tolerance (°C)
    """

    compartment_temps: dict[str, float]
    tolerance: float

    def evaluate(
        self,
        items: tuple[TemperatureItem, ...],
    ) -> tuple[bool, list[str]]:
        """评估温区隔离约束。

        Checks that items in each compartment have compatible temperature
        ranges and that compartment temperature falls within all items' ranges.

        Args:
            items: 所有温控物品 / All temperature-sensitive items

        Returns:
            tuple: (是否满足, 违规描述) / (satisfied, violation descriptions)
        """
        violations: list[str] = []
        by_compartment: dict[str, list[TemperatureItem]] = {}
        for item in items:
            by_compartment.setdefault(item.compartment_id, []).append(item)

        for comp_id, comp_items in by_compartment.items():
            comp_temp = self.compartment_temps.get(comp_id)

            for item in comp_items:
                if comp_temp is not None:
                    effective_min = item.temp_min - self.tolerance
                    effective_max = item.temp_max + self.tolerance
                    if comp_temp < effective_min or comp_temp > effective_max:
                        violations.append(
                            f"物品 {item.item_id} 温度要求 "
                            f"[{item.temp_min:.1f}, {item.temp_max:.1f}]°C "
                            f"与舱室 {comp_id} 设定 {comp_temp:.1f}°C 不兼容"
                        )

            for i in range(len(comp_items)):
                for j in range(i + 1, len(comp_items)):
                    a, b = comp_items[i], comp_items[j]
                    overlap_min = max(a.temp_min, b.temp_min)
                    overlap_max = min(a.temp_max, b.temp_max)
                    if overlap_min > overlap_max + self.tolerance:
                        violations.append(
                            f"物品 {a.item_id} "
                            f"[{a.temp_min:.1f},{a.temp_max:.1f}]°C 与 "
                            f"{b.item_id} "
                            f"[{b.temp_min:.1f},{b.temp_max:.1f}]°C "
                            f"温度范围不兼容"
                        )

        return (len(violations) == 0, violations)

    def compatible_temp_range(
        self, item_a: TemperatureItem, item_b: TemperatureItem
    ) -> tuple[float, float] | None:
        """计算两个物品的兼容温度范围。

        Args:
            item_a: 物品A / Item A
            item_b: 物品B / Item B

        Returns:
            tuple | None: 兼容范围或None / Compatible range or None
        """
        low = max(item_a.temp_min, item_b.temp_min)
        high = min(item_a.temp_max, item_b.temp_max)
        if low <= high:
            return (low, high)
        return None
