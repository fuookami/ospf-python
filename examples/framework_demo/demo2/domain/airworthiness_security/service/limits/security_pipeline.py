"""安全验证管道 / Security validation pipeline.

组合所有安全约束为统一验证管道。
Composes all security constraints into a unified
validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult
from .hazmat_airworthiness_constraint import (
    HazmatAirworthinessConstraint,
    HazmatClass,
)
from .pressure_constraint import (
    PressureConstraint,
    PressureSensitivity,
)
from .security_screening_constraint import (
    SecurityScreeningConstraint,
)
from .temperature_control_constraint import (
    TemperatureControlConstraint,
    TempZone,
)

if TYPE_CHECKING:
    from ...model.security_level import SecurityLevel


@dataclass(frozen=True)
class CargoItem:
    """待检货物项 / Cargo item to check.

    管道输入的货物信息载体。
    Cargo information carrier for pipeline input.

    Attributes:
        cargo_id: 货物标识 / Cargo identifier.
        security_level: 货物安全等级 / Cargo security level.
        hazmat_class: 危险品类别(可选) / Hazmat class (optional).
        pressure_sensitivity: 压力敏感度 / Pressure sensitivity.
        temp_zone: 温度区域 / Temperature zone.
        min_temp: 最低温度(C) / Min temperature (C).
        max_temp: 最高温度(C) / Max temperature (C).
    """

    cargo_id: str
    security_level: SecurityLevel
    hazmat_class: HazmatClass | None = None
    pressure_sensitivity: PressureSensitivity = PressureSensitivity.NONE
    temp_zone: TempZone = TempZone.AMBIENT
    min_temp: float = 15.0
    max_temp: float = 25.0


@dataclass
class SecurityPipeline:
    """安全验证管道 / Security validation pipeline.

    按顺序执行安全检查、危险品适航、温控货物、压力
    等安全约束校验，合并结果返回。
    Executes security screening, hazmat airworthiness,
    temperature control, pressure, and other security
    constraint checks in sequence, merging results for
    return.

    Attributes:
        required_level: 要求的安全等级 / Required security level.
        hold_temp_zone: 货舱温度区域 / Hold temperature zone.
        hold_pressure_diff: 货舱压差(kPa) / Hold pressure diff.
        _results: 内部结果收集 / Internal result collection.
    """

    required_level: SecurityLevel
    hold_temp_zone: TempZone = TempZone.AMBIENT
    hold_pressure_diff: float = 20.0
    _results: list[AirworthinessResult] = field(default_factory=list, init=False)

    def run(
        self,
        cargo_items: list[CargoItem],
    ) -> AirworthinessResult:
        """运行安全验证管道。

        Run the security validation pipeline.

        Args:
            cargo_items: 待检货物列表。/ Cargo items to check.

        Returns:
            合并后的安全验证结果。
            Merged security validation result.
        """
        self._results.clear()

        for item in cargo_items:
            self._check_screening(item)
            self._check_hazmat(item)
            self._check_temperature(item)
            self._check_pressure(item)

        return self._merge_results()

    def _check_screening(self, item: CargoItem) -> None:
        """校验安全检查等级 / Check screening level.

        Args:
            item: 货物项。/ Cargo item.
        """
        constraint = SecurityScreeningConstraint(
            cargo_level=item.security_level,
            required_level=self.required_level,
            cargo_id=item.cargo_id,
        )
        self._results.append(constraint.check())

    def _check_hazmat(self, item: CargoItem) -> None:
        """校验危险品 / Check hazardous materials.

        Args:
            item: 货物项。/ Cargo item.
        """
        if item.hazmat_class is None:
            return

        constraint = HazmatAirworthinessConstraint(
            hazmat_class=item.hazmat_class,
            cargo_id=item.cargo_id,
            cargo_security_level=item.security_level,
        )
        self._results.append(constraint.check())

    def _check_temperature(self, item: CargoItem) -> None:
        """校验温控 / Check temperature control.

        Args:
            item: 货物项。/ Cargo item.
        """
        constraint = TemperatureControlConstraint(
            cargo_id=item.cargo_id,
            cargo_min_temp=item.min_temp,
            cargo_max_temp=item.max_temp,
            cargo_zone=item.temp_zone,
            hold_zone=self.hold_temp_zone,
        )
        self._results.append(constraint.check())

    def _check_pressure(self, item: CargoItem) -> None:
        """校验压力 / Check pressure.

        Args:
            item: 货物项。/ Cargo item.
        """
        constraint = PressureConstraint(
            cargo_id=item.cargo_id,
            sensitivity=item.pressure_sensitivity,
            hold_pressure_diff=self.hold_pressure_diff,
        )
        self._results.append(constraint.check())

    def _merge_results(self) -> AirworthinessResult:
        """合并所有结果 / Merge all results.

        Returns:
            合并后的结果。
            Merged result.
        """
        if not self._results:
            return AirworthinessResult.create_pass()

        merged = self._results[0]
        for r in self._results[1:]:
            merged = merged.merge(r)
        return merged

    def check_all_pass(self, cargo_items: list[CargoItem]) -> bool:
        """快速检查是否全部通过。

        Quick check whether all cargo items pass.

        Args:
            cargo_items: 待检货物列表。/ Cargo items to check.

        Returns:
            全部通过返回 True。
            True if all items pass.
        """
        return self.run(cargo_items).is_pass

    def violations_summary(self, cargo_items: list[CargoItem]) -> str:
        """生成违规摘要 / Generate violations summary.

        Args:
            cargo_items: 待检货物列表。/ Cargo items to check.

        Returns:
            可读的违规摘要文本。
            Human-readable violations summary text.
        """
        result = self.run(cargo_items)
        if result.is_pass:
            return "All cargo items passed security checks."

        lines = [
            f"Status: {result.status}",
            f"Violations ({result.violation_count}):",
        ]
        for i, v in enumerate(result.violations, 1):
            lines.append(f"  {i}. {v}")
        return "\n".join(lines)
