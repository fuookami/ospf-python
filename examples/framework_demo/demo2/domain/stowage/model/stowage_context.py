"""装载上下文 / Stowage context.

管理装载规划的运行时上下文和注册表。
Manages the runtime context and registry for stowage planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.stowage_aggregation import (
    StowageAggregation,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_constraint import (
        StowageConstraint,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_plan import (
        StowagePlan,
    )


@dataclass(frozen=True)
class StowageContext:
    """装载上下文 / Stowage context.

    作为装载域对应用层暴露的建模入口，管理货舱注册表、
    货物注册表、约束注册表和聚合状态。
    Serves as the modeling entry point exposed to the application
    layer, managing compartment registry, item registry,
    constraint registry, and aggregation state.

    Attributes:
        aggregation: 装载聚合 / Stowage aggregation.
        compartments: 已注册货舱 / Registered compartments.
        items: 已注册货物 / Registered items.
        constraints: 已注册约束 / Registered constraints.
    """

    aggregation: StowageAggregation = field(
        default_factory=StowageAggregation,
    )
    """装载聚合 / Stowage aggregation."""

    compartments: tuple[StowageCompartment, ...] = field(
        default_factory=tuple,
    )
    """已注册货舱 / Registered compartments."""

    items: tuple[StowageItem, ...] = field(
        default_factory=tuple,
    )
    """已注册货物 / Registered items."""

    constraints: tuple[StowageConstraint, ...] = field(
        default_factory=tuple,
    )
    """已注册约束 / Registered constraints."""

    # ==================== 注册 / Registration =====================

    def register_compartment(
        self,
        compartment: StowageCompartment,
    ) -> StowageContext:
        """注册货舱。

        Register a compartment.

        Args:
            compartment: 待注册的货舱。/ Compartment to register.

        Returns:
            包含新货舱的上下文副本。
            A new context with the compartment registered.
        """
        return StowageContext(
            aggregation=self.aggregation,
            compartments=self.compartments + (compartment,),
            items=self.items,
            constraints=self.constraints,
        )

    def register_item(
        self,
        item: StowageItem,
    ) -> StowageContext:
        """注册货物。

        Register an item.

        Args:
            item: 待注册的货物。/ Item to register.

        Returns:
            包含新货物的上下文副本。
            A new context with the item registered.
        """
        return StowageContext(
            aggregation=self.aggregation,
            compartments=self.compartments,
            items=self.items + (item,),
            constraints=self.constraints,
        )

    def register_constraint(
        self,
        constraint: StowageConstraint,
    ) -> StowageContext:
        """注册约束。

        Register a constraint.

        Args:
            constraint: 待注册的约束。/ Constraint to register.

        Returns:
            包含新约束的上下文副本。
            A new context with the constraint registered.
        """
        return StowageContext(
            aggregation=self.aggregation,
            compartments=self.compartments,
            items=self.items,
            constraints=self.constraints + (constraint,),
        )

    def register_plan(
        self,
        plan: StowagePlan,
    ) -> StowageContext:
        """注册装载方案。

        Register a stowage plan.

        Args:
            plan: 待注册的方案。/ Plan to register.

        Returns:
            包含新方案的上下文副本。
            A new context with the plan registered.
        """
        return StowageContext(
            aggregation=self.aggregation.with_plan(plan),
            compartments=self.compartments,
            items=self.items,
            constraints=self.constraints,
        )

    # ==================== 查询 / Queries =========================

    def compartment_by_id(
        self,
        comp_id: str,
    ) -> StowageCompartment | None:
        """按标识查找货舱。

        Find compartment by identifier.

        Args:
            comp_id: 舱室标识。/ Compartment identifier.

        Returns:
            匹配的货舱，不存在时返回 None。
            Matching compartment, or None if not found.
        """
        for comp in self.compartments:
            if comp.comp_id == comp_id:
                return comp
        return None

    def item_by_id(
        self,
        item_id: str,
    ) -> StowageItem | None:
        """按标识查找货物。

        Find item by identifier.

        Args:
            item_id: 货物标识。/ Item identifier.

        Returns:
            匹配的货物，不存在时返回 None。
            Matching item, or None if not found.
        """
        for item in self.items:
            if item.item_id == item_id:
                return item
        return None

    def constraints_by_type(
        self,
        constraint_type: str,
    ) -> tuple[StowageConstraint, ...]:
        """按类型查找约束。

        Find constraints by type.

        Args:
            constraint_type: 约束类型。/ Constraint type.

        Returns:
            匹配的约束元组。/ Tuple of matching constraints.
        """
        return tuple(
            c for c in self.constraints if c.constraint_type == constraint_type
        )

    # ==================== 统计 / Statistics ========================

    @property
    def total_registered_weight(self) -> float:
        """已注册货物总重量。

        Total weight of registered items.

        Returns:
            所有注册货物的重量之和（千克）。
            Sum of all registered item weights (kg).
        """
        return sum(item.weight for item in self.items)

    @property
    def total_compartment_capacity(self) -> float:
        """货舱总容量。

        Total compartment weight capacity.

        Returns:
            所有货舱的最大重量之和（千克）。
            Sum of all compartment max weights (kg).
        """
        return sum(c.max_weight for c in self.compartments)

    def remaining_capacity(
        self,
        comp_id: str,
    ) -> float:
        """计算指定货舱的剩余重量容量。

        Calculate remaining weight capacity for a compartment.

        Args:
            comp_id: 舱室标识。/ Compartment identifier.

        Returns:
            剩余容量（千克），货舱不存在时返回 0.0。
            Remaining capacity (kg), or 0.0 if compartment not found.
        """
        comp = self.compartment_by_id(comp_id)
        if comp is None:
            return 0.0
        return comp.remaining_weight(0.0)
