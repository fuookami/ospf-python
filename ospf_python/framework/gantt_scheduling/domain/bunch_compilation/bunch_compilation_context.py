"""束编组编译上下文 / Bunch compilation context.

束编组编译域的建模入口，负责初始化聚合并注册到优化模型。
The modeling entry point for the bunch compilation domain,
responsible for initializing aggregation and registering
to the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
    BunchCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_model import (
    BunchCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.service.limits.bunch_capacity_constraint import (
    BunchCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.service.limits.bunch_demand_constraint import (
    BunchDemandConstraint,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.assignment import (
        BunchAssignment,
    )
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_modeling_config import (
        BunchCompilationModelingConfig,
    )
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.capacity import (
        BunchCapacity,
    )
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.load import (
        BunchLoad,
    )


@dataclass(frozen=True)
class BunchCompilationContext:
    """束编组编译上下文 / Bunch compilation context.

    作为束编组编译域对应用层暴露的建模入口，管理聚合状态
    和优化模型。提供分配注册、容量管理和约束构建功能。
    Serves as the modeling entry point exposed to the application
    layer, managing aggregation state and the optimization model.
    Provides assignment registration, capacity management, and
    constraint construction.

    Attributes:
        aggregation: 束编组聚合 / Bunch compilation aggregation.
        model: 优化模型 / Optimization model.
    """

    aggregation: BunchCompilationAggregation = field(
        default_factory=BunchCompilationAggregation,
    )
    model: BunchCompilationModel = field(
        default_factory=BunchCompilationModel,
    )

    # ==================== 注册 / Registration ================

    def register_assignment(
        self,
        assignment: BunchAssignment,
    ) -> BunchCompilationContext:
        """注册分配决策。

        Register an assignment decision.

        Args:
            assignment: 分配决策。/ Assignment decision.

        Returns:
            包含新分配的上下文副本。
            A new context with the assignment registered.
        """
        return BunchCompilationContext(
            aggregation=self.aggregation.with_assignment(
                assignment,
            ),
            model=self.model,
        )

    def register_capacity(
        self,
        capacity: BunchCapacity,
    ) -> BunchCompilationContext:
        """注册容量记录。

        Register a capacity record.

        Args:
            capacity: 容量记录。/ Capacity record.

        Returns:
            包含新容量记录的上下文副本。
            A new context with the capacity registered.
        """
        return BunchCompilationContext(
            aggregation=self.aggregation.with_capacity(
                capacity,
            ),
            model=self.model,
        )

    def register_load(
        self,
        load: BunchLoad,
    ) -> BunchCompilationContext:
        """注册负载记录。

        Register a load record.

        Args:
            load: 负载记录。/ Load record.

        Returns:
            包含新负载记录的上下文副本。
            A new context with the load registered.
        """
        return BunchCompilationContext(
            aggregation=self.aggregation.with_load(load),
            model=self.model,
        )

    # ==================== 查询 / Queries =====================

    def get_assignment(
        self,
        *,
        item_key: str,
        bunch_key: str,
    ) -> BunchAssignment | None:
        """按标识查找分配。

        Find an assignment by item and bunch key.

        Args:
            item_key: 物料项标识。/ Item identifier.
            bunch_key: 束编组标识。/ Bunch identifier.

        Returns:
            匹配的分配，不存在时返回 None。
            Matching assignment, or None if not found.
        """
        return self.aggregation.get_assignment(
            item_key=item_key,
            bunch_key=bunch_key,
        )

    def assignments_for_item(
        self,
        item_key: str,
    ) -> tuple[BunchAssignment, ...]:
        """获取指定物料项的所有分配。

        Get all assignments for a specific item.

        Args:
            item_key: 物料项标识。/ Item identifier.

        Returns:
            分配元组。/ Tuple of assignments.
        """
        return self.aggregation.assignments_for_item(item_key)

    def remaining_capacity(
        self,
        bunch_key: str,
    ) -> float:
        """获取指定束编组的剩余容量。

        Get remaining capacity for a specific bunch.

        Args:
            bunch_key: 束编组标识。/ Bunch identifier.

        Returns:
            剩余容量，不存在时返回 0.0。
            Remaining capacity, or 0.0 if not found.
        """
        cap = self.aggregation.get_capacity(bunch_key)
        if cap is None:
            return 0.0
        return float(cap.remaining_capacity)

    # ==================== 约束构建 / Constraint building =======

    def build_capacity_constraints(
        self,
    ) -> tuple[BunchCapacity, ...]:
        """构建容量约束 / Build capacity constraints.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraints.
        """
        constraint = BunchCapacityConstraint()
        return constraint.build_constraints(self.aggregation)

    def check_demand_feasibility(
        self,
    ) -> bool:
        """检查需求可行性 / Check demand feasibility.

        Returns:
            若所有需求均可满足则返回 True。
            True if all demands can be satisfied.
        """
        constraint = BunchDemandConstraint()
        return constraint.is_feasible(self.aggregation)

    # ==================== 配置 / Configuration ================

    def with_config(
        self,
        config: BunchCompilationModelingConfig,
    ) -> BunchCompilationContext:
        """创建不同配置的上下文副本。

        Create a context copy with different config.

        Args:
            config: 新的建模配置。/ New modeling config.

        Returns:
            配置更新后的上下文副本。/ Updated context copy.
        """
        return BunchCompilationContext(
            aggregation=self.aggregation,
            model=self.model.with_config(config),
        )
