"""甘特调度问题定义 / Gantt scheduling problem definition.

封装列生成所需的完整问题数据：任务、资源和优先关系。
Encapsulates the complete problem data required for column
generation: tasks, resources, and precedence relations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
        Resource,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
        Task,
    )


@dataclass(frozen=True)
class PrecedenceRelation:
    """优先关系 / Precedence relation.

    表示两个任务之间的先后约束。
    Represents a precedence constraint between two tasks.

    Attributes:
        predecessor_key: 前置任务键 / Predecessor task key.
        successor_key: 后续任务键 / Successor task key.
        min_gap: 最小间隔时间（秒）/ Minimum gap (seconds).
    """

    predecessor_key: str
    successor_key: str
    min_gap: float = 0.0


@dataclass(frozen=True)
class GanttProblem:
    """甘特调度问题 / Gantt scheduling problem.

    包含列生成算法所需的全部输入数据：任务集合、
    资源集合和任务间的优先关系。
    Contains all input data required by the column generation
    algorithm: task set, resource set, and precedence relations
    among tasks.

    Attributes:
        name: 问题名称 / Problem name.
        tasks: 任务集合 / Task set.
        resources: 资源集合 / Resource set.
        precedence_relations: 优先关系集合 / Precedence relation set.
        time_horizon: 调度时间范围（秒）/ Scheduling horizon (seconds).
    """

    name: str = "gantt problem"
    tasks: tuple[Task, ...] = ()
    resources: tuple[Resource, ...] = ()
    precedence_relations: tuple[PrecedenceRelation, ...] = ()
    time_horizon: float = float("inf")

    # ==================== 验证 / Validation =====================

    def validate(self) -> Result[None, str, Err[str]]:
        """验证问题数据完整性 / Validate problem data integrity.

        检查任务键唯一性、资源引用有效性和优先关系合法性。
        Checks task key uniqueness, resource reference validity,
        and precedence relation legality.

        Returns:
            验证成功返回 Ok(None)，否则返回错误。
            Ok(None) on success, error otherwise.
        """
        if len(self.tasks) == 0:
            return Failed(
                Err(
                    _code=ErrorCode.ILLEGAL_ARGUMENT,
                    _message=(
                        "问题必须包含至少一个任务 / "
                        "Problem must contain at least one task"
                    ),
                )
            )

        key_dup = self._find_duplicate_task_keys()
        if key_dup is not None:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(f"任务键重复: {key_dup} / Duplicate task key: {key_dup}"),
                )
            )

        res_ref = self._find_invalid_resource_reference()
        if res_ref is not None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(
                        f"任务引用了未知资源: {res_ref} / "
                        f"Task references unknown resource: "
                        f"{res_ref}"
                    ),
                )
            )

        prec_err = self._find_invalid_precedence()
        if prec_err is not None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(
                        f"优先关系中任务未找到: {prec_err} / "
                        f"Task not found in precedence: "
                        f"{prec_err}"
                    ),
                )
            )

        return Ok(None)

    # ==================== 查询 / Queries =========================

    @property
    def task_keys(self) -> tuple[str, ...]:
        """获取所有任务键 / Get all task keys.

        Returns:
            任务键元组 / Task key tuple.
        """
        return tuple(t.task_key for t in self.tasks)

    @property
    def resource_keys(self) -> tuple[str, ...]:
        """获取所有资源键 / Get all resource keys.

        Returns:
            资源键元组 / Resource key tuple.
        """
        return tuple(r.resource_key for r in self.resources)

    @property
    def task_count(self) -> int:
        """获取任务数量 / Get task count.

        Returns:
            任务数量 / Number of tasks.
        """
        return len(self.tasks)

    @property
    def resource_count(self) -> int:
        """获取资源数量 / Get resource count.

        Returns:
            资源数量 / Number of resources.
        """
        return len(self.resources)

    @property
    def precedence_count(self) -> int:
        """获取优先关系数量 / Get precedence relation count.

        Returns:
            优先关系数量 / Number of precedence relations.
        """
        return len(self.precedence_relations)

    def task_by_key(self, key: str) -> Task | None:
        """按键查找任务 / Find task by key.

        Args:
            key: 任务键 / Task key.

        Returns:
            匹配的任务或 None / Matching task or None.
        """
        for task in self.tasks:
            if task.task_key == key:
                return task
        return None

    def resource_by_key(self, key: str) -> Resource | None:
        """按键查找资源 / Find resource by key.

        Args:
            key: 资源键 / Resource key.

        Returns:
            匹配的资源或 None / Matching resource or None.
        """
        for resource in self.resources:
            if resource.resource_key == key:
                return resource
        return None

    def successors_of(self, task_key: str) -> tuple[str, ...]:
        """获取指定任务的所有后继任务键 / Get successor keys.

        Args:
            task_key: 前置任务键 / Predecessor task key.

        Returns:
            后继任务键元组 / Successor task key tuple.
        """
        return tuple(
            rel.successor_key
            for rel in self.precedence_relations
            if rel.predecessor_key == task_key
        )

    def predecessors_of(
        self,
        task_key: str,
    ) -> tuple[str, ...]:
        """获取指定任务的所有前驱任务键 / Get predecessor keys.

        Args:
            task_key: 后续任务键 / Successor task key.

        Returns:
            前驱任务键元组 / Predecessor task key tuple.
        """
        return tuple(
            rel.predecessor_key
            for rel in self.precedence_relations
            if rel.successor_key == task_key
        )

    def filter_by_priority(
        self,
        min_priority: int,
    ) -> tuple[Task, ...]:
        """按优先级过滤任务 / Filter tasks by priority.

        Args:
            min_priority: 最低优先级 / Minimum priority.

        Returns:
            满足优先级要求的任务元组。
            Task tuple meeting priority requirement.
        """
        return tuple(t for t in self.tasks if t.priority >= min_priority)

    def tasks_for_resource(
        self,
        resource_key: str,
    ) -> tuple[Task, ...]:
        """获取需要指定资源的任务 / Get tasks requiring a resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            需要该资源的任务元组。
            Task tuple requiring the resource.
        """
        return tuple(t for t in self.tasks if t.requires_resource(resource_key))

    def has_task(self, task_key: str) -> bool:
        """检查是否包含指定任务 / Check if contains a task.

        Args:
            task_key: 任务键 / Task key.

        Returns:
            包含该任务时返回 True / True when containing.
        """
        return any(t.task_key == task_key for t in self.tasks)

    def has_resource(self, resource_key: str) -> bool:
        """检查是否包含指定资源 / Check if contains a resource.

        Args:
            resource_key: 资源键 / Resource key.

        Returns:
            包含该资源时返回 True / True when containing.
        """
        return any(r.resource_key == resource_key for r in self.resources)

    # ==================== 内部验证 / Internal validation =========

    def _find_duplicate_task_keys(self) -> str | None:
        """查找重复的任务键 / Find duplicate task keys.

        Returns:
            第一个重复的任务键，无重复时返回 None。
            First duplicate task key, None if no duplicates.
        """
        seen: set[str] = set()
        for task in self.tasks:
            if task.task_key in seen:
                return task.task_key
            seen.add(task.task_key)
        return None

    def _find_invalid_resource_reference(self) -> str | None:
        """查找无效的资源引用 / Find invalid resource references.

        Returns:
            第一个无效的资源键，全部有效时返回 None。
            First invalid resource key, None if all valid.
        """
        resource_set = set(self.resource_keys)
        for task in self.tasks:
            for res_key, _ in task.resource_requirements:
                if res_key not in resource_set:
                    return res_key
        return None

    def _find_invalid_precedence(self) -> str | None:
        """查找无效的优先关系 / Find invalid precedence relations.

        Returns:
            第一个无效的任务键，全部有效时返回 None。
            First invalid task key, None if all valid.
        """
        task_set = set(self.task_keys)
        for rel in self.precedence_relations:
            if rel.predecessor_key not in task_set:
                return rel.predecessor_key
            if rel.successor_key not in task_set:
                return rel.successor_key
        return None
