"""航空器模型定义 / Aircraft model definition.

航空器及其运行约束的封装模型。
Wrapper model for aircraft and its operating constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.model.deck import Deck
    from examples.framework_demo.demo2.domain.aircraft.model.fuel import Fuel
    from examples.framework_demo.demo2.domain.aircraft.model.fuselage import Fuselage
    from examples.framework_demo.demo2.domain.aircraft.model.hatch_door import HatchDoor
    from examples.framework_demo.demo2.domain.aircraft.model.uld import ULD


@dataclass(frozen=True)
class AircraftConstraints:
    """航空器约束 / Aircraft constraints.

    封装航空器运行中的各类约束参数。
    Encapsulates various constraint parameters during
    aircraft operations.

    Attributes:
        min_fuel_reserve_ratio: 最低燃油储备比例 / Min fuel reserve ratio.
        max_cg_offset: 最大重心偏移量 (m) / Max CG offset (m).
        cargo_density_limit: 货物密度上限 (kg/m^3) / Cargo density limit (kg/m^3).
    """

    min_fuel_reserve_ratio: float
    """最低燃油储备比例 / Min fuel reserve ratio."""

    max_cg_offset: float
    """最大重心偏移量 (m) / Max CG offset (m)."""

    cargo_density_limit: float
    """货物密度上限 (kg/m^3) / Cargo density limit (kg/m^3)."""

    @staticmethod
    def default() -> AircraftConstraints:
        """创建默认约束 / Create default constraints.

        Returns:
            默认约束实例 / Default constraints instance.
        """
        return AircraftConstraints(
            min_fuel_reserve_ratio=0.05,
            max_cg_offset=2.0,
            cargo_density_limit=500.0,
        )


@dataclass(frozen=True)
class AircraftModel:
    """航空器模型 / Aircraft model.

    将航空器实体与其运行约束、甲板布局和集装器
    类型组合为完整的业务模型。
    Combines the aircraft entity with operating constraints,
    deck layout, and ULD types into a complete business model.

    Attributes:
        aircraft: 航空器实体 / Aircraft entity.
        constraints: 运行约束 / Operating constraints.
        decks: 甲板列表 / List of decks.
        supported_ulds: 支持的集装器类型 / Supported ULD types.
        fuel: 燃油类型 / Fuel type.
        fuselage: 机身参数 / Fuselage parameters.
        hatch_doors: 舱门列表 / List of hatch doors.
    """

    aircraft: Aircraft
    """航空器实体 / Aircraft entity."""

    constraints: AircraftConstraints
    """运行约束 / Operating constraints."""

    decks: tuple[Deck, ...]
    """甲板列表 / List of decks."""

    supported_ulds: tuple[ULD, ...]
    """支持的集装器类型 / Supported ULD types."""

    fuel: Fuel
    """燃油类型 / Fuel type."""

    fuselage: Fuselage
    """机身参数 / Fuselage parameters."""

    hatch_doors: tuple[HatchDoor, ...]
    """舱门列表 / List of hatch doors."""

    @staticmethod
    def create(
        *,
        aircraft: Aircraft,
        constraints: AircraftConstraints,
        decks: tuple[Deck, ...],
        supported_ulds: tuple[ULD, ...],
        fuel: Fuel,
        fuselage: Fuselage,
        hatch_doors: tuple[HatchDoor, ...] = (),
    ) -> AircraftModel:
        """创建航空器模型 / Create aircraft model.

        Args:
            aircraft: 航空器实体 / Aircraft entity.
            constraints: 运行约束 / Operating constraints.
            decks: 甲板列表 / List of decks.
            supported_ulds: 支持的集装器类型 / Supported ULD types.
            fuel: 燃油类型 / Fuel type.
            fuselage: 机身参数 / Fuselage parameters.
            hatch_doors: 舱门列表，默认空 / Hatch doors, default empty.

        Returns:
            航空器模型实例 / Aircraft model instance.
        """
        return AircraftModel(
            aircraft=aircraft,
            constraints=constraints,
            decks=decks,
            supported_ulds=supported_ulds,
            fuel=fuel,
            fuselage=fuselage,
            hatch_doors=hatch_doors,
        )

    @property
    def total_deck_volume(self) -> float:
        """所有甲板总体积 / Total volume of all decks.

        Returns:
            甲板体积总和 (m^3) / Sum of deck volumes (m^3).
        """
        return sum(d.volume for d in self.decks)

    @property
    def total_deck_load_capacity(self) -> float:
        """所有甲板总承载量 / Total load capacity of all decks.

        Returns:
            甲板承载量总和 (kg) / Sum of deck max loads (kg).
        """
        return sum(d.max_load for d in self.decks)

    def deck_by_id(self, deck_id: str) -> Deck | None:
        """按标识查找甲板 / Lookup deck by ID.

        Args:
            deck_id: 甲板标识 / Deck identifier.

        Returns:
            匹配的甲板或 None / Matching deck or None.
        """
        for deck in self.decks:
            if deck.deck_id == deck_id:
                return deck
        return None

    def uld_by_type(self, uld_type: str) -> ULD | None:
        """按类型查找集装器 / Lookup ULD by type.

        Args:
            uld_type: 集装器类型代码 / ULD type code.

        Returns:
            匹配的集装器或 None / Matching ULD or None.
        """
        for uld in self.supported_ulds:
            if uld.uld_type == uld_type:
                return uld
        return None

    def with_constraints(self, constraints: AircraftConstraints) -> AircraftModel:
        """创建不同约束的模型 / Create model with different constraints.

        Args:
            constraints: 新约束 / New constraints.

        Returns:
            新模型实例 / New model instance.
        """
        return AircraftModel(
            aircraft=self.aircraft,
            constraints=constraints,
            decks=self.decks,
            supported_ulds=self.supported_ulds,
            fuel=self.fuel,
            fuselage=self.fuselage,
            hatch_doors=self.hatch_doors,
        )
