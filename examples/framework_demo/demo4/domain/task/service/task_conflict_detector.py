"""Task conflict detector service.

任务冲突检测服务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ..model.task_conflict import ConflictType, TaskConflict

if TYPE_CHECKING:
    from ..model.flight_task import FlightTask
    from ..model.task_schedule import TaskSchedule


class TaskConflictDetector:
    """Detects scheduling conflicts among flight tasks.

    检测航班任务间的调度冲突。
    """

    def detect_time_overlaps(
        self,
        schedules: Sequence[TaskSchedule],
    ) -> Sequence[TaskConflict]:
        """Detect time overlaps between scheduled tasks.

        检测调度任务间的时间重叠。

        Args:
            schedules: Task schedules to check.

        Returns:
            Sequence of detected time overlap conflicts.
        """
        conflicts: list[TaskConflict] = []
        sorted_schedules = sorted(schedules, key=lambda s: s.planned_start)

        for i, sched_a in enumerate(sorted_schedules):
            for sched_b in sorted_schedules[i + 1 :]:
                if sched_b.planned_start >= sched_a.planned_end:
                    break
                conflicts.append(
                    TaskConflict(
                        task_a=sched_a.task_id,
                        task_b=sched_b.task_id,
                        conflict_type=(ConflictType.TIME_OVERLAP),
                    )
                )

        return tuple(conflicts)

    def detect_resource_conflicts(
        self,
        tasks: Sequence[FlightTask],
    ) -> Sequence[TaskConflict]:
        """Detect tasks using same aircraft at same time.

        检测同时使用同一飞机的任务。

        Args:
            tasks: Flight tasks to check.

        Returns:
            Sequence of detected resource conflicts.
        """
        conflicts: list[TaskConflict] = []
        by_aircraft: dict[str, list[FlightTask]] = {}

        for task in tasks:
            by_aircraft.setdefault(task.aircraft_type, []).append(task)

        for _aircraft_type, aircraft_tasks in by_aircraft.items():
            sorted_tasks = sorted(
                aircraft_tasks,
                key=lambda t: t.departure_time,
            )
            for i, task_a in enumerate(sorted_tasks):
                for task_b in sorted_tasks[i + 1 :]:
                    if task_b.departure_time >= task_a.arrival_time:
                        break
                    if task_a.origin == task_b.origin:
                        conflicts.append(
                            TaskConflict(
                                task_a=task_a.task_id,
                                task_b=task_b.task_id,
                                conflict_type=(ConflictType.RESOURCE_CONFLICT),
                            )
                        )

        return tuple(conflicts)

    def detect_all(
        self,
        tasks: Sequence[FlightTask],
        schedules: Sequence[TaskSchedule],
    ) -> Sequence[TaskConflict]:
        """Run all conflict detection checks.

        运行所有冲突检测检查。

        Args:
            tasks: Flight tasks to check.
            schedules: Task schedules to check.

        Returns:
            All detected conflicts combined.
        """
        time_conflicts = self.detect_time_overlaps(schedules)
        resource_conflicts = self.detect_resource_conflicts(tasks)
        return list(time_conflicts) + list(resource_conflicts)
