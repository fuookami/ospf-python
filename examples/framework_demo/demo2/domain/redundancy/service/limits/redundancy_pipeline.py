"""冗余分析管道 / Redundancy analysis pipeline.

组合所有冗余约束为统一验证管道。
Composes all redundancy constraints into a unified
validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.redundancy_result import RedundancyResult
from .backup_availability_constraint import (
    BackupAvailabilityConstraint,
)
from .redundancy_level_constraint import (
    RedundancyLevelConstraint,
)
from .single_point_failure_constraint import (
    SinglePointFailureConstraint,
)

if TYPE_CHECKING:
    from ...model.redundancy_aggregation import (
        RedundancyAggregation,
    )
    from ...model.redundancy_component import (
        RedundancyComponent,
    )
    from ...model.redundancy_context import RedundancyContext


@dataclass(frozen=True)
class RedundancyPipelineConfig:
    """冗余管道配置 / Redundancy pipeline configuration.

    控制管道中启用哪些约束。
    Controls which constraints are enabled in the pipeline.

    Attributes:
        enable_spof: 启用单点故障约束 /
            Enable SPOF constraint.
        enable_level: 启用冗余等级约束 /
            Enable redundancy level constraint.
        enable_availability: 启用备份可用性约束 /
            Enable backup availability constraint.
        min_redundancy_level: 最低冗余等级 /
            Minimum redundancy level.
        min_availability: 最低可用度 /
            Minimum availability.
    """

    enable_spof: bool = True
    enable_level: bool = True
    enable_availability: bool = True
    min_redundancy_level: int = 1
    min_availability: float = 0.99


@dataclass
class RedundancyPipeline:
    """冗余分析管道 / Redundancy analysis pipeline.

    按顺序执行单点故障检查、冗余等级检查和备份可用性
    检查，合并结果返回。
    Executes single point of failure, redundancy level,
    and backup availability checks in sequence, merging
    results for return.

    Attributes:
        context: 冗余上下文 / Redundancy context.
        config: 管道配置 / Pipeline configuration.
        _results: 内部结果收集 / Internal result collection.
    """

    context: RedundancyContext
    config: RedundancyPipelineConfig = field(
        default_factory=RedundancyPipelineConfig,
    )
    _results: list[RedundancyResult] = field(
        default_factory=list,
        init=False,
    )

    def run(
        self,
        *,
        system_id: str,
        components: tuple[RedundancyComponent, ...],
    ) -> RedundancyResult:
        """运行冗余分析管道。

        Run the redundancy analysis pipeline.

        Args:
            system_id: 系统标识 / System identifier.
            components: 系统组件列表 / System component list.

        Returns:
            合并后的冗余分析结果。
            Merged redundancy analysis result.
        """
        self._results.clear()

        if self.config.enable_spof:
            self._check_spof(system_id, components)

        if self.config.enable_level:
            self._check_level(system_id, components)

        if self.config.enable_availability:
            self._check_availability(system_id, components)

        self._check_context()

        return self._merge_results(system_id)

    def _check_spof(
        self,
        system_id: str,
        components: tuple[RedundancyComponent, ...],
    ) -> None:
        """校验单点故障 / Check single point of failure.

        Args:
            system_id: 系统标识 / System identifier.
            components: 组件列表 / Component list.
        """
        constraint = SinglePointFailureConstraint(
            system_id=system_id,
        )
        self._results.append(
            constraint.check(components),
        )

    def _check_level(
        self,
        system_id: str,
        components: tuple[RedundancyComponent, ...],
    ) -> None:
        """校验冗余等级 / Check redundancy level.

        Args:
            system_id: 系统标识 / System identifier.
            components: 组件列表 / Component list.
        """
        constraint = RedundancyLevelConstraint(
            system_id=system_id,
            min_level=self.config.min_redundancy_level,
        )
        self._results.append(
            constraint.check(components),
        )

    def _check_availability(
        self,
        system_id: str,
        components: tuple[RedundancyComponent, ...],
    ) -> None:
        """校验备份可用性 / Check backup availability.

        Args:
            system_id: 系统标识 / System identifier.
            components: 组件列表 / Component list.
        """
        constraint = BackupAvailabilityConstraint(
            system_id=system_id,
            min_availability=self.config.min_availability,
        )
        self._results.append(
            constraint.check(components),
        )

    def _check_context(self) -> None:
        """校验上下文基础项 / Check context basics."""
        ctx_result = self.context.validate()
        self._results.append(ctx_result)

    def _merge_results(
        self,
        system_id: str,
    ) -> RedundancyResult:
        """合并所有结果 / Merge all results.

        Args:
            system_id: 系统标识 / System identifier.

        Returns:
            合并后的结果 / Merged result.
        """
        if not self._results:
            return RedundancyResult.create_compliant(
                system_id=system_id,
                redundancy_level=0,
            )

        merged = self._results[0]
        for r in self._results[1:]:
            merged = merged.merge(r)
        return merged

    def run_all_systems(
        self,
        *,
        systems: dict[
            str,
            tuple[RedundancyComponent, ...],
        ],
    ) -> RedundancyAggregation:
        """运行所有系统的冗余分析。

        Run redundancy analysis for all systems.

        Args:
            systems: 系统标识->组件列表映射 /
                System ID -> component list mapping.

        Returns:
            所有系统的聚合结果 / Aggregation of all systems.
        """
        from ...model.redundancy_aggregation import (
            RedundancyAggregation,
        )

        results: list[RedundancyResult] = []
        for sys_id, comps in systems.items():
            result = self.run(
                system_id=sys_id,
                components=comps,
            )
            results.append(result)
        return RedundancyAggregation(
            results=tuple(results),
        )
