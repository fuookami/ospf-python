"""Bunch context for managing the bunch registry.

任务组上下文管理 / Bunch context for registry management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bunch import Bunch


class BunchContext:
    """Registry and lookup service for scheduling bunches.

    调度任务组的注册表与查询服务。
    """

    def __init__(self) -> None:
        self._registry: dict[str, Bunch] = {}

    def register(self, bunch: Bunch) -> None:
        """Register a bunch in the context.

        在上下文中注册一个任务组。
        """
        self._registry[bunch.bunch_id] = bunch

    def unregister(self, bunch_id: str) -> bool:
        """Remove a bunch from the registry. Returns True if found.

        从注册表中移除任务组。找到则返回 True。
        """
        if bunch_id in self._registry:
            del self._registry[bunch_id]
            return True
        return False

    def lookup(self, bunch_id: str) -> Bunch | None:
        """Look up a bunch by its identifier.

        通过标识符查找任务组。
        """
        return self._registry.get(bunch_id)

    def all_bunches(self) -> tuple[Bunch, ...]:
        """Return all registered bunches.

        返回所有已注册的任务组。
        """
        return tuple(self._registry.values())

    def by_resource_type(
        self,
        resource_type: str,
    ) -> tuple[Bunch, ...]:
        """Filter bunches by resource type.

        按资源类型筛选任务组。
        """
        return tuple(
            bunch
            for bunch in self._registry.values()
            if bunch.resource_type == resource_type
        )

    def by_time_range(
        self,
        *,
        start: float,
        end: float,
    ) -> tuple[Bunch, ...]:
        """Filter bunches that overlap with the given time range.

        筛选与给定时间范围重叠的任务组。
        """
        return tuple(
            bunch
            for bunch in self._registry.values()
            if bunch.start_time < end and start < bunch.end_time
        )

    @property
    def size(self) -> int:
        """Number of registered bunches.

        已注册任务组数量。
        """
        return len(self._registry)

    def clear(self) -> None:
        """Remove all registered bunches.

        移除所有已注册的任务组。
        """
        self._registry.clear()
