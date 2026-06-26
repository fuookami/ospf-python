"""燃油定义 / Fuel definition.

航空燃油属性定义。
Aviation fuel property definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuel:
    """燃油 / Fuel.

    描述航空燃油的物理属性和成本信息。
    Describes physical properties and cost of aviation fuel.

    Attributes:
        fuel_type: 燃油类型 / Fuel type name.
        density: 燃油密度 (kg/L) / Fuel density (kg/L).
        specific_energy: 比能量 (MJ/kg) / Specific energy (MJ/kg).
        unit_cost: 单位成本 (元/L) / Unit cost (CNY/L).
    """

    fuel_type: str
    """燃油类型 / Fuel type name."""

    density: float
    """燃油密度 (kg/L) / Fuel density (kg/L)."""

    specific_energy: float
    """比能量 (MJ/kg) / Specific energy (MJ/kg)."""

    unit_cost: float
    """单位成本 (元/L) / Unit cost (CNY/L)."""

    @staticmethod
    def create(
        *,
        fuel_type: str,
        density: float,
        specific_energy: float,
        unit_cost: float,
    ) -> Fuel:
        """创建燃油实例 / Create fuel instance.

        Args:
            fuel_type: 燃油类型 / Fuel type name.
            density: 燃油密度 (kg/L) / Fuel density (kg/L).
            specific_energy: 比能量 (MJ/kg) / Specific energy (MJ/kg).
            unit_cost: 单位成本 (元/L) / Unit cost (CNY/L).

        Returns:
            燃油实例 / Fuel instance.
        """
        return Fuel(
            fuel_type=fuel_type,
            density=density,
            specific_energy=specific_energy,
            unit_cost=unit_cost,
        )

    @staticmethod
    def jet_a1() -> Fuel:
        """创建 Jet A-1 燃油实例 / Create Jet A-1 fuel instance.

        Jet A-1 是最常用的航空煤油。
        Jet A-1 is the most common aviation kerosene.

        Returns:
            Jet A-1 燃油实例 / Jet A-1 fuel instance.
        """
        return Fuel(
            fuel_type="Jet A-1",
            density=0.804,
            specific_energy=43.15,
            unit_cost=6.5,
        )

    def weight_from_volume(self, volume: float) -> float:
        """根据体积计算重量 / Calculate weight from volume.

        Args:
            volume: 燃油体积 (L) / Fuel volume (L).

        Returns:
            燃油重量 (kg) / Fuel weight (kg).
        """
        return volume * self.density

    def volume_from_weight(self, weight: float) -> float:
        """根据重量计算体积 / Calculate volume from weight.

        Args:
            weight: 燃油重量 (kg) / Fuel weight (kg).

        Returns:
            燃油体积 (L) / Fuel volume (L).
        """
        return weight / self.density

    def cost_for_volume(self, volume: float) -> float:
        """计算指定体积的燃油成本 / Calculate fuel cost for volume.

        Args:
            volume: 燃油体积 (L) / Fuel volume (L).

        Returns:
            燃油成本 (元) / Fuel cost (CNY).
        """
        return volume * self.unit_cost

    def with_unit_cost(self, unit_cost: float) -> Fuel:
        """创建不同单价的燃油 / Create fuel with different unit cost.

        Args:
            unit_cost: 新单位成本 / New unit cost.

        Returns:
            新燃油实例 / New fuel instance.
        """
        return Fuel(
            fuel_type=self.fuel_type,
            density=self.density,
            specific_energy=self.specific_energy,
            unit_cost=unit_cost,
        )
