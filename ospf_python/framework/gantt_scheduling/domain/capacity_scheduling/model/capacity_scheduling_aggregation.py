"""Gantt scheduling capacity scheduling aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapacitySchedulingAggregation:
    """Gantt scheduling capacity scheduling aggregation."""

    name: str = "capacity_scheduling_aggregation"
    _assignments: tuple[Any, ...] = ()
    _capacities: tuple[Any, ...] = ()
    _loads: tuple[Any, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    @property
    def work_item_keys(self) -> tuple[str, ...]:
        """获取工作项标识。/ Get work item keys."""
        return tuple(
            dict.fromkeys(getattr(a, "work_item_key", "") for a in self._assignments)
        )

    @property
    def capacities(self) -> tuple[Any, ...]:
        """获取已注册容量记录。/ Get registered capacities."""
        return self._capacities

    def with_assignment(
        self,
        assignment: Any,
    ) -> CapacitySchedulingAggregation:
        """创建包含新分配的聚合副本。/ Copy with new assignment."""
        return CapacitySchedulingAggregation(
            name=self.name,
            _assignments=(*self._assignments, assignment),
            _capacities=self._capacities,
            _loads=self._loads,
        )

    def with_capacity(
        self,
        capacity: Any,
    ) -> CapacitySchedulingAggregation:
        """创建包含新容量的聚合副本。/ Copy with new capacity."""
        return CapacitySchedulingAggregation(
            name=self.name,
            _assignments=self._assignments,
            _capacities=(*self._capacities, capacity),
            _loads=self._loads,
        )

    def with_load(
        self,
        load: Any,
    ) -> CapacitySchedulingAggregation:
        """创建包含新负载的聚合副本。/ Copy with new load."""
        return CapacitySchedulingAggregation(
            name=self.name,
            _assignments=self._assignments,
            _capacities=self._capacities,
            _loads=(*self._loads, load),
        )

    def get_capacity(
        self,
        capacity_slot_key: str,
    ) -> Any | None:
        """按标识查找容量。/ Find capacity by key."""
        for c in self._capacities:
            if getattr(c, "capacity_slot_key", None) == capacity_slot_key:
                return c
        return None

    def assignments_for_work_item(
        self,
        work_item_key: str,
    ) -> tuple[Any, ...]:
        """获取指定工作项的分配。/ Get assignments for work item."""
        return tuple(
            a
            for a in self._assignments
            if getattr(a, "work_item_key", None) == work_item_key
        )

    def total_load_for_slot(
        self,
        capacity_slot_key: str,
    ) -> float:
        """计算指定槽的总负载。/ Compute total load for slot."""
        return sum(
            getattr(ld, "load_amount", 0.0)
            for ld in self._loads
            if (getattr(ld, "capacity_slot_key", None) == capacity_slot_key)
        )
