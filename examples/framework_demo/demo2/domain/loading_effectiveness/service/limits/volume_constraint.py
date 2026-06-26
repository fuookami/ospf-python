"""体积约束。

Volume constraint enforcing capacity limits per compartment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.compartment_loading import CompartmentLoading


@dataclass(frozen=True)
class VolumeConstraint:
    """舱室体积约束。

    Enforces that the volume of items in each compartment does not
    exceed its maximum capacity.

    Attributes:
        max_volumes: 各舱室最大体积映射 / Mapping of compartment_id to max volume (m³)
    """

    max_volumes: dict[str, float]

    def evaluate(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> tuple[bool, dict[str, float]]:
        """评估装载方案是否满足体积约束。

        Evaluates whether each compartment's volume is within limits.

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            tuple: (是否全部满足, 各舱室剩余容量) / (all satisfied, remaining capacities)
        """
        remaining: dict[str, float] = {}
        all_satisfied = True
        for comp in compartments:
            max_vol = self.max_volumes.get(comp.compartment_id, float("inf"))
            leftover = max_vol - comp.volume
            remaining[comp.compartment_id] = leftover
            if leftover < 0.0:
                all_satisfied = False
        return (all_satisfied, remaining)

    def can_fit(
        self,
        compartment_id: str,
        current_volume: float,
        item_volume: float,
    ) -> bool:
        """判断物品能否放入指定舱室。

        Args:
            compartment_id: 舱室标识 / Compartment ID
            current_volume: 当前已用体积 / Current used volume
            item_volume: 待装物品体积 / Item volume to add

        Returns:
            bool: 是否放得下 / Whether item fits
        """
        max_vol = self.max_volumes.get(compartment_id, float("inf"))
        return (current_volume + item_volume) <= max_vol

    def utilization_ratios(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> dict[str, float]:
        """计算各舱室体积利用率。

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            dict: 各舱室利用率 / Utilization ratio per compartment
        """
        ratios: dict[str, float] = {}
        for comp in compartments:
            max_vol = self.max_volumes.get(comp.compartment_id, 0.0)
            if max_vol <= 0.0:
                ratios[comp.compartment_id] = 0.0
            else:
                ratios[comp.compartment_id] = min(comp.volume / max_vol, 1.0)
        return ratios
