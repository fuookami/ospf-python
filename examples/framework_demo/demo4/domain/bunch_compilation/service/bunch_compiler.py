"""Bunch compiler for grouping tasks into scheduling bunches.

任务组编译器：将任务分组为调度任务组。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..model.bunch import Bunch

if TYPE_CHECKING:
    from ..model.bunch_context import BunchContext


@dataclass(frozen=True)
class TaskInput:
    """Input task descriptor for compilation.

    用于编译的输入任务描述符。
    """

    task_id: str
    resource_type: str
    start_time: float
    end_time: float


class BunchCompiler:
    """Compiles individual tasks into scheduling bunches.

    将单个任务编译为调度任务组。
    """

    def __init__(
        self,
        *,
        context: BunchContext,
        max_gap: float = 60.0,
    ) -> None:
        self._context = context
        self._max_gap = max_gap

    def compile_tasks(
        self,
        tasks: tuple[TaskInput, ...],
    ) -> tuple[Bunch, ...]:
        """Group tasks by resource type and temporal proximity.

        按资源类型和时间邻近性对任务进行分组。
        """
        by_resource = self._group_by_resource(tasks)
        all_bunches: list[Bunch] = []
        for resource_type, group in by_resource.items():
            sorted_tasks = sorted(
                group,
                key=lambda t: t.start_time,
            )
            bunches = self._cluster_by_time(
                resource_type,
                sorted_tasks,
            )
            all_bunches.extend(bunches)
        for bunch in all_bunches:
            self._context.register(bunch)
        return tuple(all_bunches)

    def _group_by_resource(
        self,
        tasks: tuple[TaskInput, ...],
    ) -> dict[str, list[TaskInput]]:
        """Group tasks by their resource type.

        按资源类型对任务进行分组。
        """
        groups: dict[str, list[TaskInput]] = {}
        for task in tasks:
            groups.setdefault(task.resource_type, []).append(
                task,
            )
        return groups

    def _cluster_by_time(
        self,
        resource_type: str,
        sorted_tasks: list[TaskInput],
    ) -> list[Bunch]:
        """Cluster temporally close tasks into bunches.

        将时间上接近的任务聚类为任务组。
        """
        if not sorted_tasks:
            return []
        bunches: list[Bunch] = []
        current_ids: list[str] = [sorted_tasks[0].task_id]
        current_start = sorted_tasks[0].start_time
        current_end = sorted_tasks[0].end_time
        for task in sorted_tasks[1:]:
            gap = task.start_time - current_end
            if gap <= self._max_gap:
                current_ids.append(task.task_id)
                current_end = max(current_end, task.end_time)
            else:
                bunches.append(
                    self._make_bunch(
                        resource_type=resource_type,
                        task_ids=tuple(current_ids),
                        start=current_start,
                        end=current_end,
                    )
                )
                current_ids = [task.task_id]
                current_start = task.start_time
                current_end = task.end_time
        bunches.append(
            self._make_bunch(
                resource_type=resource_type,
                task_ids=tuple(current_ids),
                start=current_start,
                end=current_end,
            )
        )
        return bunches

    def _make_bunch(
        self,
        *,
        resource_type: str,
        task_ids: tuple[str, ...],
        start: float,
        end: float,
    ) -> Bunch:
        """Create a Bunch with a generated identifier.

        创建带有生成标识符的任务组。
        """
        bunch_id = f"bunch_{resource_type}_{start:.0f}_{end:.0f}"
        return Bunch(
            bunch_id=bunch_id,
            tasks=task_ids,
            resource_type=resource_type,
            start_time=start,
            end_time=end,
        )
