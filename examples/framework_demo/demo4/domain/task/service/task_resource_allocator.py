"""Task resource allocator service.

任务资源分配服务。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ..model.flight_task import FlightTask
    from ..model.task_requirement import TaskRequirement


@dataclass(frozen=True)
class Allocation:
    """Resource allocation for a single task.

    单个任务的资源分配。
    """

    task_id: str
    """ID of the allocated task.

    被分配任务的 ID。
    """

    aircraft_type: str
    """Allocated aircraft type.

    分配的飞机类型。
    """

    crew_ids: tuple[str, ...] = ()
    """Allocated crew member IDs.

    分配的机组成员 ID。
    """

    @property
    def crew_count(self) -> int:
        """Number of allocated crew members.

        分配的机组成员数量。
        """
        return len(self.crew_ids)


@dataclass(frozen=True)
class AllocationResult:
    """Result of a resource allocation operation.

    资源分配操作的结果。
    """

    allocations: tuple[Allocation, ...] = ()
    """Successful allocations.

    成功的分配。
    """

    unallocated_task_ids: tuple[str, ...] = ()
    """Tasks that could not be allocated.

    无法分配的任务。
    """

    @property
    def allocated_count(self) -> int:
        """Number of successfully allocated tasks.

        成功分配的任务数量。
        """
        return len(self.allocations)

    @property
    def all_allocated(self) -> bool:
        """Whether all tasks were allocated.

        是否所有任务都已分配。
        """
        return len(self.unallocated_task_ids) == 0


class TaskResourceAllocator:
    """Allocates aircraft and crew resources to tasks.

    将飞机和机组资源分配给任务。
    """

    def __init__(self) -> None:
        """Initialize the resource allocator.

        初始化资源分配器。
        """
        self._available_aircraft: dict[str, list[str]] = {}
        self._available_crew: dict[str, list[str]] = {}

    def set_available_aircraft(
        self,
        aircraft_type: str,
        aircraft_ids: Sequence[str],
    ) -> None:
        """Set available aircraft of a given type.

        设置给定类型的可用飞机。

        Args:
            aircraft_type: Aircraft type code.
            aircraft_ids: Available aircraft IDs.
        """
        self._available_aircraft[aircraft_type] = list(aircraft_ids)

    def set_available_crew(
        self,
        aircraft_type: str,
        crew_ids: Sequence[str],
    ) -> None:
        """Set available crew qualified for a type.

        设置有资格操作某类型的可用机组。

        Args:
            aircraft_type: Aircraft type code.
            crew_ids: Available crew IDs.
        """
        self._available_crew[aircraft_type] = list(crew_ids)

    def allocate(
        self,
        tasks: Sequence[FlightTask],
        requirements: Sequence[TaskRequirement],
    ) -> AllocationResult:
        """Allocate resources to tasks based on requirements.

        根据需求将资源分配给任务。

        Args:
            tasks: Tasks needing resource allocation.
            requirements: Resource requirements per task.

        Returns:
            AllocationResult with allocations.
        """
        req_map = {r.task_id: r for r in requirements}
        allocations: list[Allocation] = []
        unallocated: list[str] = []

        aircraft_pool: dict[str, list[str]] = {
            k: list(v) for k, v in self._available_aircraft.items()
        }
        crew_pool: dict[str, list[str]] = {
            k: list(v) for k, v in self._available_crew.items()
        }

        for task in tasks:
            req = req_map.get(task.task_id)
            aircraft = self._allocate_aircraft(
                task.aircraft_type,
                aircraft_pool,
            )
            if aircraft is None:
                unallocated.append(task.task_id)
                continue

            crew_count = req.crew_count if req else 2
            crew = self._allocate_crew(
                task.aircraft_type,
                crew_count,
                crew_pool,
            )
            if len(crew) < crew_count:
                unallocated.append(task.task_id)
                continue

            allocations.append(
                Allocation(
                    task_id=task.task_id,
                    aircraft_type=task.aircraft_type,
                    crew_ids=tuple(crew),
                )
            )

        return AllocationResult(
            allocations=tuple(allocations),
            unallocated_task_ids=tuple(unallocated),
        )

    def _allocate_aircraft(
        self,
        aircraft_type: str,
        pool: dict[str, list[str]],
    ) -> str | None:
        """Allocate one aircraft from the pool.

        从池中分配一架飞机。

        Args:
            aircraft_type: Required aircraft type.
            pool: Available aircraft pool.

        Returns:
            Aircraft ID if available, None otherwise.
        """
        available = pool.get(aircraft_type, [])
        if not available:
            return None
        return available.pop(0)

    def _allocate_crew(
        self,
        aircraft_type: str,
        count: int,
        pool: dict[str, list[str]],
    ) -> list[str]:
        """Allocate crew members from the pool.

        从池中分配机组成员。

        Args:
            aircraft_type: Aircraft type to crew.
            count: Number of crew needed.
            pool: Available crew pool.

        Returns:
            List of allocated crew IDs.
        """
        available = pool.get(aircraft_type, [])
        allocated: list[str] = []
        for _ in range(count):
            if not available:
                break
            allocated.append(available.pop(0))
        return allocated
