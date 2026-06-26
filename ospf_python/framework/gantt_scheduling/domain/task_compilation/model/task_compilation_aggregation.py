"""Gantt scheduling task compilation aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskCompilationAggregation:
    """Gantt scheduling task compilation aggregation."""

    name: str = "task_compilation_aggregation"
    _tasks: tuple[Any, ...] = ()
    _assignments: tuple[Any, ...] = ()
    _capacities: tuple[Any, ...] = ()
    _loads: tuple[Any, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    @property
    def tasks(self) -> tuple[Any, ...]:
        """获取已注册任务。/ Get registered tasks."""
        return self._tasks

    @property
    def assignments(self) -> tuple[Any, ...]:
        """获取已注册分配。/ Get registered assignments."""
        return self._assignments

    @property
    def capacities(self) -> tuple[Any, ...]:
        """获取已注册容量记录。/ Get registered capacities."""
        return self._capacities

    @property
    def loads(self) -> tuple[Any, ...]:
        """获取已注册负载记录。/ Get registered loads."""
        return self._loads

    def with_task(self, task: Any) -> TaskCompilationAggregation:
        """创建包含新任务的聚合副本。/ Create copy with new task."""
        return TaskCompilationAggregation(
            name=self.name,
            _tasks=(*self._tasks, task),
            _assignments=self._assignments,
            _capacities=self._capacities,
            _loads=self._loads,
        )

    def with_assignment(
        self,
        assignment: Any,
    ) -> TaskCompilationAggregation:
        """创建包含新分配的聚合副本。/ Create copy with new assignment."""
        return TaskCompilationAggregation(
            name=self.name,
            _tasks=self._tasks,
            _assignments=(*self._assignments, assignment),
            _capacities=self._capacities,
            _loads=self._loads,
        )

    def with_capacity(
        self,
        capacity: Any,
    ) -> TaskCompilationAggregation:
        """创建包含新容量的聚合副本。/ Create copy with new capacity."""
        return TaskCompilationAggregation(
            name=self.name,
            _tasks=self._tasks,
            _assignments=self._assignments,
            _capacities=(*self._capacities, capacity),
            _loads=self._loads,
        )

    def with_load(self, load: Any) -> TaskCompilationAggregation:
        """创建包含新负载的聚合副本。/ Create copy with new load."""
        return TaskCompilationAggregation(
            name=self.name,
            _tasks=self._tasks,
            _assignments=self._assignments,
            _capacities=self._capacities,
            _loads=(*self._loads, load),
        )

    def get_task(self, task_key: str) -> Any | None:
        """按标识查找任务。/ Find task by key."""
        for t in self._tasks:
            if getattr(t, "task_key", None) == task_key:
                return t
        return None

    def assignments_for_task(
        self,
        task_key: str,
    ) -> tuple[Any, ...]:
        """获取指定任务的分配。/ Get assignments for a task."""
        return tuple(
            a for a in self._assignments if getattr(a, "task_key", None) == task_key
        )

    def assignments_for_resource(
        self,
        resource_key: str,
    ) -> tuple[Any, ...]:
        """获取指定资源的分配。/ Get assignments for a resource."""
        return tuple(
            a
            for a in self._assignments
            if getattr(a, "resource_key", None) == resource_key
        )

    def total_load_for_resource(
        self,
        resource_key: str,
    ) -> float:
        """计算指定资源的总负载。/ Compute total load for resource."""
        return sum(
            getattr(ld, "load_amount", 0.0)
            for ld in self._loads
            if getattr(ld, "resource_key", None) == resource_key
        )

    def total_capacity_for_resource(
        self,
        resource_key: str,
    ) -> float:
        """计算指定资源的总容量。/ Compute total capacity for resource."""
        return sum(
            getattr(c, "max_capacity", 0.0)
            for c in self._capacities
            if getattr(c, "resource_key", None) == resource_key
        )

    def capacity_for(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> Any | None:
        """查找精确匹配的容量记录。/ Find exact capacity record."""
        for c in self._capacities:
            if (
                getattr(c, "resource_key", None) == resource_key
                and getattr(c, "window_start", None) == window_start
                and getattr(c, "window_end", None) == window_end
            ):
                return c
        return None
