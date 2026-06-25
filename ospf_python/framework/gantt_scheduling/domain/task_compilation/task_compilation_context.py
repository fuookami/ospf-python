"""任务编译上下文 / Task compilation context.

任务编译域的建模入口，负责初始化聚合并注册到优化模型。
The modeling entry point for the task compilation domain,
responsible for initializing aggregation and registering
to the optimization model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_aggregation import (
    TaskCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_aliases import (
    ConstraintEntry,
    VariableEntry,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_model import (
    TaskCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_modeling_config import (
    TaskCompilationModelingConfig,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.task.model.task import (
        Task,
    )
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.assignment import (
        Assignment,
    )
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.capacity import (
        Capacity,
    )
    from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.load import (
        Load,
    )


@dataclass(frozen=True)
class TaskCompilationContext:
    """任务编译上下文 / Task compilation context.

    作为任务编译域对应用层暴露的建模入口，管理任务、
    分配、容量和负载的注册与查询。
    提供模型构建和可行性检查能力。
    Serves as the modeling entry point exposed to the
    application layer, managing registration and querying
    of tasks, assignments, capacities, and loads.
    Provides model building and feasibility checking.

    Attributes:
        aggregation: 任务编译聚合 / Task compilation
            aggregation.
        config: 建模配置 / Modeling config.
    """

    aggregation: TaskCompilationAggregation = field(
        default_factory=TaskCompilationAggregation,
    )
    config: TaskCompilationModelingConfig = field(
        default_factory=TaskCompilationModelingConfig,
    )

    # ==================== 注册 / Registration ==================

    def register_task(
        self,
        task: Task,
    ) -> TaskCompilationContext:
        """注册新任务。

        Register a new task.

        Args:
            task: 待注册的任务。/ Task to register.

        Returns:
            包含新任务的 TaskCompilationContext 副本。
            A new TaskCompilationContext with the task
            registered.
        """
        return TaskCompilationContext(
            aggregation=self.aggregation.with_task(task),
            config=self.config,
        )

    def register_assignment(
        self,
        assignment: Assignment,
    ) -> TaskCompilationContext:
        """注册任务分配。

        Register a task assignment.

        Args:
            assignment: 待注册的分配。/ Assignment to
                register.

        Returns:
            包含新分配的 TaskCompilationContext 副本。
            A new TaskCompilationContext with the assignment
            registered.
        """
        return TaskCompilationContext(
            aggregation=self.aggregation.with_assignment(
                assignment,
            ),
            config=self.config,
        )

    def register_capacity(
        self,
        capacity: Capacity,
    ) -> TaskCompilationContext:
        """注册资源容量记录。

        Register a resource capacity record.

        Args:
            capacity: 容量记录。/ Capacity record.

        Returns:
            包含新容量记录的 TaskCompilationContext 副本。
            A new TaskCompilationContext with the capacity
            registered.
        """
        return TaskCompilationContext(
            aggregation=self.aggregation.with_capacity(
                capacity,
            ),
            config=self.config,
        )

    def register_load(
        self,
        load: Load,
    ) -> TaskCompilationContext:
        """注册资源负载。

        Register a resource load.

        Args:
            load: 待注册的负载。/ Load to register.

        Returns:
            包含新负载的 TaskCompilationContext 副本。
            A new TaskCompilationContext with the load
            registered.
        """
        return TaskCompilationContext(
            aggregation=self.aggregation.with_load(load),
            config=self.config,
        )

    # ==================== 查询 / Queries ========================

    def get_task(
        self,
        task_key: str,
    ) -> Task | None:
        """按标识查找任务。

        Find a task by its key.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            匹配的任务，不存在时返回 None。
            Matching task, or None if not found.
        """
        return self.aggregation.get_task(task_key)

    def get_all_tasks(self) -> tuple[Task, ...]:
        """获取所有已注册任务。

        Get all registered tasks.

        Returns:
            任务元组。/ Tuple of tasks.
        """
        return self.aggregation.tasks

    def assignments_for_task(
        self,
        task_key: str,
    ) -> tuple[Assignment, ...]:
        """获取指定任务的所有分配。

        Get all assignments for a specific task.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            分配元组。/ Tuple of assignments.
        """
        return self.aggregation.assignments_for_task(
            task_key,
        )

    # ==================== 容量与负载 / Capacity and load =======

    def total_load_for_resource(
        self,
        resource_key: str,
    ) -> float:
        """计算指定资源的总负载。

        Compute total load for a resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            总负载量。/ Total load amount.
        """
        return self.aggregation.total_load_for_resource(
            resource_key,
        )

    def total_capacity_for_resource(
        self,
        resource_key: str,
    ) -> float:
        """计算指定资源的总容量。

        Compute total capacity for a resource.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            总容量。/ Total capacity.
        """
        return self.aggregation.total_capacity_for_resource(
            resource_key,
        )

    def remaining_capacity(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> float:
        """计算指定资源在时间窗口内的剩余容量。

        Compute remaining capacity of a resource within
        a time window.

        查找精确匹配的容量记录；若不存在，则用总容量
        减去窗口内的总负载作为估算。
        Looks up an exact capacity record; if absent,
        estimates as total capacity minus total in-window
        load.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            剩余容量，资源不存在时返回 0.0。
            Remaining capacity, or 0.0 if resource not
            found.
        """
        cap = self.aggregation.capacity_for(
            resource_key=resource_key,
            window_start=window_start,
            window_end=window_end,
        )
        if cap is not None:
            return max(
                0.0,
                cap.max_capacity
                - sum(
                    ld.load_amount
                    for ld in self.aggregation.loads
                    if ld.resource_key == resource_key
                ),
            )
        total_cap = self.total_capacity_for_resource(
            resource_key,
        )
        total_load = self.total_load_for_resource(
            resource_key,
        )
        if total_cap == 0.0 and total_load == 0.0:
            return 0.0
        return max(0.0, total_cap - total_load)

    # ==================== 模型构建 / Model building ============

    def build_model(self) -> TaskCompilationModel:
        """从当前聚合状态构建优化模型。

        Build optimization model from current aggregation
        state.

        为每个任务-资源分配生成决策变量，为每条容量
        记录生成容量约束。
        Generates decision variables for each task-resource
        assignment and capacity constraints for each capacity
        record.

        Returns:
            构建完成的优化模型。
            The constructed optimization model.
        """
        model = TaskCompilationModel(
            model_name="task_compilation",
        )
        model = self._add_assignment_variables(model)
        model = self._add_capacity_constraints(model)
        return model

    def _add_assignment_variables(
        self,
        model: TaskCompilationModel,
    ) -> TaskCompilationModel:
        """为所有分配添加决策变量。

        Add decision variables for all assignments.
        """
        current = model
        for a in self.aggregation.assignments:
            var_name = f"x_{a.task_key}_{a.resource_key}"
            coeff = self._objective_coefficient(
                task_key=a.task_key,
                resource_key=a.resource_key,
            )
            current = current.add_variable(
                VariableEntry(
                    name=var_name,
                    lower_bound=0.0,
                    upper_bound=1.0,
                    is_integer=True,
                    coefficient=coeff,
                ),
            )
        return current

    def _add_capacity_constraints(
        self,
        model: TaskCompilationModel,
    ) -> TaskCompilationModel:
        """为所有容量记录添加约束。

        Add constraints for all capacity records.
        """
        current = model
        for cap in self.aggregation.capacities:
            related = self.aggregation.assignments_for_resource(
                cap.resource_key,
            )
            coeffs = tuple(
                (
                    f"x_{a.task_key}_{a.resource_key}",
                    1.0,
                )
                for a in related
            )
            name = f"cap_{cap.resource_key}_{cap.window_start}_{cap.window_end}"
            current = current.add_constraint(
                ConstraintEntry(
                    name=name,
                    coefficients=coeffs,
                    sense="<=",
                    rhs=cap.max_capacity,
                ),
            )
        return current

    def _objective_coefficient(
        self,
        *,
        task_key: str,
        resource_key: str,
    ) -> float:
        """计算目标函数系数。

        Compute objective function coefficient.

        基于任务优先级和默认权重计算。
        Based on task priority and default weight.
        """
        task = self.aggregation.get_task(task_key)
        if task is None:
            return self.config.default_objective_weight
        priority_factor = max(1, task.priority + 1)
        return self.config.default_objective_weight * priority_factor

    # ==================== 可行性 / Feasibility ==================

    def is_feasible(self) -> bool:
        """检查所有容量约束是否满足。

        Check whether all capacity constraints are
        satisfied.

        遍历每个资源，验证总负载不超过总容量。
        Iterates over each resource, verifying that total
        load does not exceed total capacity.

        Returns:
            若所有资源负载均在容量范围内则返回 True。
            True if all resource loads are within capacity
            bounds.
        """
        resource_keys = {c.resource_key for c in self.aggregation.capacities}
        for rk in resource_keys:
            cap = self.total_capacity_for_resource(rk)
            load = self.total_load_for_resource(rk)
            if load > cap + self.config.precision:
                return False
        return True
