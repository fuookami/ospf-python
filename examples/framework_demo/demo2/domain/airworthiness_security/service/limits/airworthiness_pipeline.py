"""适航验证管道 / Airworthiness validation pipeline.

组合所有适航约束为统一验证管道。
Composes all airworthiness constraints into a unified
validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.airworthiness_result import AirworthinessResult
from .cg_envelope_constraint import CGEnvelopeConstraint
from .clim_constraint import CLIMConstraint
from .cumulative_load_constraint import CumulativeLoadConstraint
from .linear_density_constraint import LinearDensityConstraint
from .max_weight_envelope_constraint import (
    MaxWeightEnvelopeConstraint,
)
from .structural_floor_constraint import StructuralFloorConstraint

if TYPE_CHECKING:
    from ...model.airworthiness_aggregation import (
        AirworthinessAggregation,
    )
    from ...model.airworthiness_context import AirworthinessContext


@dataclass
class AirworthinessPipeline:
    """适航验证管道 / Airworthiness validation pipeline.

    按顺序执行重量包线、重心包线、地板载荷、累积载荷、
    CLIM、线密度等适航约束校验，合并结果返回。
    Executes weight envelope, CG envelope, floor loading,
    cumulative load, CLIM, linear density, and other
    airworthiness constraint checks in sequence, merging
    results for return.

    Attributes:
        context: 适航上下文 / Airworthiness context.
        _results: 内部结果收集 / Internal result collection.
    """

    context: AirworthinessContext
    _results: list[AirworthinessResult] = field(default_factory=list, init=False)

    def run(
        self,
        *,
        total_weight: float,
        cg_position: float,
        floor_loads: dict[str, float] | None = None,
        cumulative_additions: dict[float, float] | None = None,
        clim_loads: dict[str, float] | None = None,
        density_checks: list[tuple[float, float, float, float]] | None = None,
    ) -> AirworthinessResult:
        """运行适航验证管道。

        Run the airworthiness validation pipeline.

        Args:
            total_weight: 当前总重量(kg) / Current total weight (kg).
            cg_position: 当前重心(%MAC) / Current CG (%MAC).
            floor_loads: 区域->施加载荷映射 /
                Area -> applied load mapping.
            cumulative_additions: 站位->新增重量映射 /
                Station -> additional weight mapping.
            clim_loads: CLIM键->载荷指数映射 /
                CLIM key -> load index mapping.
            density_checks: 线密度检查列表[(位置, 密度, 长度, 上限)] /
                Linear density check list.

        Returns:
            合并后的适航验证结果。
            Merged airworthiness validation result.
        """
        self._results.clear()
        aggregation = self.context.build_aggregation()

        self._check_weight_envelope(aggregation, total_weight)
        self._check_cg_envelope(aggregation, cg_position)
        self._check_floor_loads(aggregation, floor_loads or {})
        self._check_cumulative_loads(aggregation, cumulative_additions or {})
        self._check_clims(aggregation, clim_loads or {})
        self._check_linear_densities(density_checks or [])
        self._check_context()

        return self._merge_results()

    def _check_weight_envelope(
        self,
        aggregation: AirworthinessAggregation,
        total_weight: float,
    ) -> None:
        """校验重量包线 / Check weight envelopes.

        Args:
            aggregation: 适航聚合。/ Airworthiness aggregation.
            total_weight: 总重量(kg)。/ Total weight (kg).
        """
        for envelope in aggregation.envelopes:
            constraint = MaxWeightEnvelopeConstraint(
                envelope=envelope,
            )
            result = constraint.check(total_weight)
            self._results.append(result)

    def _check_cg_envelope(
        self,
        aggregation: AirworthinessAggregation,
        cg_position: float,
    ) -> None:
        """校验重心包线 / Check CG envelopes.

        Args:
            aggregation: 适航聚合。/ Airworthiness aggregation.
            cg_position: 重心位置(%MAC)。/ CG position (%MAC).
        """
        for envelope in aggregation.envelopes:
            constraint = CGEnvelopeConstraint(
                envelope=envelope,
            )
            result = constraint.check(cg_position)
            self._results.append(result)

    def _check_floor_loads(
        self,
        aggregation: AirworthinessAggregation,
        floor_loads: dict[str, float],
    ) -> None:
        """校验地板载荷 / Check floor loads.

        Args:
            aggregation: 适航聚合。/ Airworthiness aggregation.
            floor_loads: 区域->施加载荷映射。
                Area -> applied load mapping.
        """
        for area_id, applied in floor_loads.items():
            fl = aggregation.find_floor_loading(area_id)
            if fl is not None:
                constraint = StructuralFloorConstraint(
                    floor_loading=fl,
                )
                result = constraint.check(applied)
                self._results.append(result)

    def _check_cumulative_loads(
        self,
        aggregation: AirworthinessAggregation,
        additions: dict[float, float],
    ) -> None:
        """校验累积载荷 / Check cumulative loads.

        Args:
            aggregation: 适航聚合。/ Airworthiness aggregation.
            additions: 站位->新增重量映射。
                Station -> additional weight mapping.
        """
        for cl in aggregation.cumulative_loads:
            addition = additions.get(cl.position, 0.0)
            if addition > 0.0:
                constraint = CumulativeLoadConstraint(
                    load_limit=cl,
                    additional_weight=addition,
                )
                result = constraint.check()
                self._results.append(result)

    def _check_clims(
        self,
        aggregation: AirworthinessAggregation,
        clim_loads: dict[str, float],
    ) -> None:
        """校验CLIM / Check CLIMs.

        Args:
            aggregation: 适航聚合。/ Airworthiness aggregation.
            clim_loads: CLIM键->载荷指数映射。
                CLIM key -> load index mapping.
        """
        for clim in aggregation.max_clims:
            key = f"{clim.deck.value}:{clim.flight_phase.value}"
            if key in clim_loads:
                constraint = CLIMConstraint(
                    max_clim=clim,
                    current_load_index=clim_loads[key],
                )
                result = constraint.check()
                self._results.append(result)

    def _check_linear_densities(
        self,
        checks: list[tuple[float, float, float, float]],
    ) -> None:
        """校验线密度 / Check linear densities.

        Args:
            checks: (位置, 密度, 长度, 上限) 列表。
                List of (position, density, length, limit).
        """
        for position, density, length, limit in checks:
            from ...model.linear_density import LinearDensity

            ld = LinearDensity(
                position=position,
                density=density,
                length=length,
            )
            constraint = LinearDensityConstraint(
                density=ld,
                max_density=limit,
            )
            result = constraint.check()
            self._results.append(result)

    def _check_context(self) -> None:
        """校验上下文基础项 / Check context basics."""
        ctx_result = self.context.validate()
        self._results.append(ctx_result)

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
