"""温度约束 / Temperature constraint.

确保温度敏感货物放置在温控区域内。
Ensures temperature-sensitive cargo is placed in
temperature-controlled zones.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureZone:
    """温控区域 / Temperature zone.

    描述货舱的温度控制范围。
    Describes the temperature control range of a compartment.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        min_temp: 最低温度（摄氏度）/
            Minimum temperature (Celsius).
        max_temp: 最高温度（摄氏度）/
            Maximum temperature (Celsius).
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    min_temp: float = -40.0
    """最低温度（摄氏度）/ Minimum temperature (Celsius)."""

    max_temp: float = 40.0
    """最高温度（摄氏度）/ Maximum temperature (Celsius)."""

    @property
    def temp_range(self) -> float:
        """温度范围。

        Temperature range.

        Returns:
            最高温度减最低温度。/ Max temp minus min temp.
        """
        return self.max_temp - self.min_temp

    @property
    def center_temp(self) -> float:
        """中心温度。

        Center temperature.

        Returns:
            最高和最低温度的平均值。/ Average of max and min temps.
        """
        return (self.max_temp + self.min_temp) / 2.0

    def contains_temp(self, temp: float) -> bool:
        """检查温度是否在范围内。

        Check whether temperature is within range.

        Args:
            temp: 温度（摄氏度）。/ Temperature (Celsius).

        Returns:
            温度在范围内时返回 True。
            True if temperature is within range.
        """
        return self.min_temp <= temp <= self.max_temp


@dataclass(frozen=True)
class TemperatureRequirement:
    """温度需求 / Temperature requirement.

    描述货物的温度存储要求。
    Describes temperature storage requirements for cargo.

    Attributes:
        item_id: 货物标识 / Item identifier.
        required_min: 最低要求温度（摄氏度）/
            Required minimum temperature (Celsius).
        required_max: 最高要求温度（摄氏度）/
            Required maximum temperature (Celsius).
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    required_min: float = -40.0
    """最低要求温度（摄氏度）/ Required minimum temperature."""

    required_max: float = 40.0
    """最高要求温度（摄氏度）/ Required maximum temperature."""

    def compatible_with_zone(
        self,
        zone: TemperatureZone,
    ) -> bool:
        """检查是否与温控区域兼容。

        Check whether compatible with temperature zone.

        Args:
            zone: 温控区域。/ Temperature zone.

        Returns:
            温度范围满足要求时返回 True。
            True if temperature range meets requirements.
        """
        return zone.min_temp <= self.required_min and zone.max_temp >= self.required_max


@dataclass(frozen=True)
class TemperatureViolation:
    """温度违反记录 / Temperature violation record.

    记录货物放置在不兼容温控区域的信息。
    Records cargo placed in incompatible temperature zone.

    Attributes:
        item_id: 货物标识 / Item identifier.
        compartment_id: 舱室标识 / Compartment identifier.
        requirement: 温度需求 / Temperature requirement.
        zone: 温控区域 / Temperature zone.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    requirement: TemperatureRequirement = None  # type: ignore[assignment]
    """温度需求 / Temperature requirement."""

    zone: TemperatureZone = None  # type: ignore[assignment]
    """温控区域 / Temperature zone."""


@dataclass(frozen=True)
class TemperatureConstraint:
    """温度约束 / Temperature constraint.

    验证温度敏感货物被放置在满足温度要求的货舱中。
    遍历货物分配，检查每个温度敏感货物的目标货舱
    是否具备足够的温度控制能力。
    Validates that temperature-sensitive cargo is placed in
    compartments meeting temperature requirements. Iterates
    over assignments, checking that each temperature-sensitive
    item's target compartment has sufficient temperature control.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "temperature"
    """约束名称前缀 / Constraint name prefix."""

    def check_assignments(
        self,
        *,
        requirements: tuple[TemperatureRequirement, ...],
        zones: tuple[TemperatureZone, ...],
        assignments: dict[str, str],
    ) -> tuple[TemperatureViolation, ...]:
        """检查温度约束。

        Check temperature constraints.

        Args:
            requirements: 温度需求列表。/ Temperature requirements.
            zones: 温控区域列表。/ Temperature zones.
            assignments: 货物到货舱的分配。/
                Item-to-compartment assignments.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        zone_map = {z.compartment_id: z for z in zones}
        violations: list[TemperatureViolation] = []
        for req in requirements:
            comp_id = assignments.get(req.item_id)
            if comp_id is None:
                continue
            zone = zone_map.get(comp_id)
            if zone is None:
                continue
            if not req.compatible_with_zone(zone):
                violations.append(
                    TemperatureViolation(
                        item_id=req.item_id,
                        compartment_id=comp_id,
                        requirement=req,
                        zone=zone,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        requirements: tuple[TemperatureRequirement, ...],
        zones: tuple[TemperatureZone, ...],
        assignments: dict[str, str],
    ) -> bool:
        """检查温度约束是否可行。

        Check whether temperature constraints are feasible.

        Args:
            requirements: 温度需求列表。/ Temperature requirements.
            zones: 温控区域列表。/ Temperature zones.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            所有温度需求均满足时返回 True。
            True if all temperature requirements are met.
        """
        return (
            len(
                self.check_assignments(
                    requirements=requirements,
                    zones=zones,
                    assignments=assignments,
                )
            )
            == 0
        )

    def compatible_compartments(
        self,
        *,
        requirement: TemperatureRequirement,
        zones: tuple[TemperatureZone, ...],
    ) -> tuple[str, ...]:
        """获取与温度需求兼容的货舱。

        Get compartments compatible with temperature requirement.

        Args:
            requirement: 温度需求。/ Temperature requirement.
            zones: 温控区域列表。/ Temperature zones.

        Returns:
            兼容的货舱标识元组。/ Tuple of compatible compartment IDs.
        """
        return tuple(
            z.compartment_id for z in zones if requirement.compatible_with_zone(z)
        )
