"""Gantt scheduling bunch compilation aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BunchCompilationAggregation:
    """Gantt scheduling bunch compilation aggregation."""

    name: str = "bunch_compilation_aggregation"
    _assignments: tuple[Any, ...] = ()
    _capacities: tuple[Any, ...] = ()
    _loads: tuple[Any, ...] = ()
    _items: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    @property
    def item_keys(self) -> tuple[str, ...]:
        """获取物料项标识。/ Get item keys."""
        return self._items

    @property
    def bunch_keys(self) -> tuple[str, ...]:
        """获取束编组标识。/ Get bunch keys."""
        return tuple(
            dict.fromkeys(getattr(a, "bunch_key", "") for a in self._assignments)
        )

    @property
    def assignments(self) -> tuple[Any, ...]:
        """获取已注册分配。/ Get registered assignments."""
        return self._assignments

    @property
    def capacities(self) -> tuple[Any, ...]:
        """获取已注册容量记录。/ Get registered capacities."""
        return self._capacities

    def with_assignment(
        self,
        assignment: Any,
    ) -> BunchCompilationAggregation:
        """创建包含新分配的聚合副本。/ Copy with new assignment."""
        return BunchCompilationAggregation(
            name=self.name,
            _assignments=(*self._assignments, assignment),
            _capacities=self._capacities,
            _loads=self._loads,
            _items=self._items,
        )

    def with_capacity(
        self,
        capacity: Any,
    ) -> BunchCompilationAggregation:
        """创建包含新容量的聚合副本。/ Copy with new capacity."""
        return BunchCompilationAggregation(
            name=self.name,
            _assignments=self._assignments,
            _capacities=(*self._capacities, capacity),
            _loads=self._loads,
            _items=self._items,
        )

    def with_load(
        self,
        load: Any,
    ) -> BunchCompilationAggregation:
        """创建包含新负载的聚合副本。/ Copy with new load."""
        return BunchCompilationAggregation(
            name=self.name,
            _assignments=self._assignments,
            _capacities=self._capacities,
            _loads=(*self._loads, load),
            _items=self._items,
        )

    def get_assignment(
        self,
        *,
        item_key: str,
        bunch_key: str,
    ) -> Any | None:
        """按标识查找分配。/ Find assignment by keys."""
        for a in self._assignments:
            if (
                getattr(a, "item_key", None) == item_key
                and getattr(a, "bunch_key", None) == bunch_key
            ):
                return a
        return None

    def assignments_for_item(
        self,
        item_key: str,
    ) -> tuple[Any, ...]:
        """获取指定物料项的分配。/ Get assignments for item."""
        return tuple(
            a for a in self._assignments if getattr(a, "item_key", None) == item_key
        )

    def get_capacity(self, bunch_key: str) -> Any | None:
        """按束编组标识查找容量。/ Find capacity by bunch key."""
        for c in self._capacities:
            if getattr(c, "bunch_key", None) == bunch_key:
                return c
        return None

    def total_demand_for_bunch(
        self,
        bunch_key: str,
    ) -> float:
        """计算指定束编组的总需求。/ Compute total demand for bunch."""
        return sum(
            getattr(a, "demand", 0.0)
            for a in self._assignments
            if getattr(a, "bunch_key", None) == bunch_key
        )
