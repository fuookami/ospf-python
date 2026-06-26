"""Bunch compilation pipeline composing all constraints.

任务组编译管道：组合所有约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.bunch import Bunch
    from .bunch_capacity_constraint import BunchCapacityConstraint
    from .bunch_continuity_constraint import BunchContinuityConstraint
    from .bunch_resource_constraint import BunchResourceConstraint


@dataclass(frozen=True)
class PipelineResult:
    """Result of running the compilation pipeline.

    运行编译管道的结果。
    """

    compliant: tuple[Bunch, ...]
    violations: dict[str, tuple[str, ...]]


class BunchCompilationPipeline:
    """Composes bunch constraints into a single pipeline.

    将任务组约束组合到单一管道中。
    """

    def __init__(
        self,
        *,
        capacity: BunchCapacityConstraint,
        continuity: BunchContinuityConstraint,
        resource: BunchResourceConstraint,
    ) -> None:
        self._capacity = capacity
        self._continuity = continuity
        self._resource = resource
        self._extra_constraints: list[object] = []

    def add_constraint(self, constraint: object) -> None:
        """Append an additional constraint to the pipeline.

        向管道追加额外的约束。
        """
        self._extra_constraints.append(constraint)

    def execute(
        self,
        bunches: tuple[Bunch, ...],
    ) -> PipelineResult:
        """Run all constraints and return aggregated results.

        运行所有约束并返回聚合结果。
        """
        all_violations: dict[str, tuple[str, ...]] = {}
        compliant: list[Bunch] = []
        for bunch in bunches:
            msgs: list[str] = []
            msgs.extend(self._capacity.violations(bunch))
            msgs.extend(self._continuity.violations(bunch))
            msgs.extend(self._resource.violations(bunch))
            for extra in self._extra_constraints:
                if hasattr(extra, "violations"):
                    msgs.extend(extra.violations(bunch))
            if msgs:
                all_violations[bunch.bunch_id] = tuple(
                    msgs,
                )
            else:
                compliant.append(bunch)
        return PipelineResult(
            compliant=tuple(compliant),
            violations=all_violations,
        )

    @property
    def capacity(self) -> BunchCapacityConstraint:
        """Access the capacity constraint.

        访问容量约束。
        """
        return self._capacity

    @property
    def continuity(self) -> BunchContinuityConstraint:
        """Access the continuity constraint.

        访问连续性约束。
        """
        return self._continuity

    @property
    def resource(self) -> BunchResourceConstraint:
        """Access the resource constraint.

        访问资源约束。
        """
        return self._resource
