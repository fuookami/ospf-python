"""Cargo allocator for assigning cargo to bunches.

货物分配器：将货物分配到任务组。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model.cargo import Cargo


@dataclass(frozen=True)
class BunchSlot:
    """A bunch available for cargo assignment.

    可用于货物分配的任务组槽。
    """

    bunch_id: str
    capacity: float
    destination: str


@dataclass(frozen=True)
class Allocation:
    """Result of allocating a cargo to a bunch.

    将货物分配到任务组的结果。
    """

    cargo_id: str
    bunch_id: str


class CargoAllocator:
    """Allocates cargos to bunches by destination and capacity.

    按目的地和容量将货物分配到任务组。
    """

    def allocate(
        self,
        cargos: tuple[Cargo, ...],
        bunches: tuple[BunchSlot, ...],
    ) -> tuple[Allocation, ...]:
        """Assign cargos to matching bunches.

        将货物分配到匹配的任务组。
        """
        if not cargos or not bunches:
            return ()
        dest_map: dict[str, list[BunchSlot]] = {}
        for bunch in bunches:
            dest_map.setdefault(
                bunch.destination,
                [],
            ).append(bunch)
        remaining: dict[str, float] = {b.bunch_id: b.capacity for b in bunches}
        allocations: list[Allocation] = []
        sorted_cargos = sorted(
            cargos,
            key=lambda c: c.priority,
            reverse=True,
        )
        for cargo in sorted_cargos:
            slot = self._find_best_slot(
                cargo,
                dest_map,
                remaining,
            )
            if slot is not None:
                allocations.append(
                    Allocation(
                        cargo_id=cargo.cargo_id,
                        bunch_id=slot.bunch_id,
                    )
                )
                remaining[slot.bunch_id] -= cargo.weight
        return tuple(allocations)

    def _find_best_slot(
        self,
        cargo: Cargo,
        dest_map: dict[str, list[BunchSlot]],
        remaining: dict[str, float],
    ) -> BunchSlot | None:
        """Find the best bunch slot for a cargo.

        为货物找到最佳任务组槽。
        """
        candidates = dest_map.get(
            cargo.destination,
            [],
        )
        for slot in candidates:
            available = remaining.get(slot.bunch_id, 0.0)
            if available >= cargo.weight:
                return slot
        for bunch_id, available in remaining.items():
            if available >= cargo.weight:
                for slots in dest_map.values():
                    for slot in slots:
                        if slot.bunch_id == bunch_id:
                            return slot
        return None

    def unallocated(
        self,
        cargos: tuple[Cargo, ...],
        allocations: tuple[Allocation, ...],
    ) -> tuple[Cargo, ...]:
        """Return cargos that were not allocated.

        返回未被分配的货物。
        """
        allocated_ids = {a.cargo_id for a in allocations}
        return tuple(c for c in cargos if c.cargo_id not in allocated_ids)

    def allocation_summary(
        self,
        allocations: tuple[Allocation, ...],
    ) -> dict[str, tuple[str, ...]]:
        """Group allocations by bunch id.

        按任务组 ID 分组分配结果。
        """
        groups: dict[str, list[str]] = {}
        for alloc in allocations:
            groups.setdefault(
                alloc.bunch_id,
                [],
            ).append(alloc.cargo_id)
        return {bid: tuple(cids) for bid, cids in groups.items()}
