"""空间利用率优化目标。

Space utilization objective for maximizing volume usage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.space_utilization import SpaceUtilization

if TYPE_CHECKING:
    from ...model.compartment_loading import CompartmentLoading


@dataclass(frozen=True)
class SpaceUtilizationObjective:
    """空间利用率优化目标。

    Maximizes overall space utilization across all compartments
    by computing and scoring volume usage ratios.

    Attributes:
        max_volumes: 各舱室最大体积 / Compartment max volumes (m³)
        weight: 目标权重 / Objective weight in overall scoring
    """

    max_volumes: dict[str, float]
    weight: float

    def compute(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> tuple[SpaceUtilization, float]:
        """计算总体空间利用率和得分。

        Computes aggregated space utilization across all compartments.

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            tuple: (空间利用率, 加权得分) / (SpaceUtilization, weighted score)
        """
        total_volume = 0.0
        used_volume = 0.0
        for comp in compartments:
            max_vol = self.max_volumes.get(comp.compartment_id, 0.0)
            total_volume += max_vol
            used_volume += min(comp.volume, max_vol)

        utilization = SpaceUtilization.compute(total_volume, used_volume)
        score = utilization.ratio * self.weight
        return (utilization, score)

    def per_compartment(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> dict[str, SpaceUtilization]:
        """计算各舱室的空间利用率。

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            dict: 各舱室利用率 / Per-compartment utilization
        """
        result: dict[str, SpaceUtilization] = {}
        for comp in compartments:
            max_vol = self.max_volumes.get(comp.compartment_id, 0.0)
            result[comp.compartment_id] = SpaceUtilization.compute(
                max_vol,
                comp.volume,
            )
        return result

    def efficiency_gap(
        self,
        compartments: tuple[CompartmentLoading, ...],
        target_ratio: float = 0.9,
    ) -> dict[str, float]:
        """计算各舱室与目标利用率的差距。

        Args:
            compartments: 各舱室装载状态 / Compartment loading states
            target_ratio: 目标利用率 / Target utilization ratio

        Returns:
            dict: 各舱室差距 / Gap per compartment
        """
        per_comp = self.per_compartment(compartments)
        return {
            cid: max(target_ratio - util.ratio, 0.0) for cid, util in per_comp.items()
        }
