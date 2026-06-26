"""顺序约束 / Sequence constraint.

确保货物按规定的顺序装载。
Ensures that cargo items are loaded in the required sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.sequence_limit import (
        SequenceLimit,
    )

    pass


@dataclass(frozen=True)
class SequenceViolation:
    """顺序违反记录 / Sequence violation record.

    记录装载顺序违反的信息。
    Records loading sequence violation information.

    Attributes:
        violated_limit: 被违反的顺序限制 /
            Violated sequence limit.
        actual_position_a: 货物 A 的实际位置 /
            Actual position of item A.
        actual_position_b: 货物 B 的实际位置 /
            Actual position of item B.
    """

    violated_limit: SequenceLimit = None  # type: ignore[assignment]
    """被违反的顺序限制 / Violated sequence limit."""

    actual_position_a: int = 0
    """货物 A 的实际位置 / Actual position of item A."""

    actual_position_b: int = 0
    """货物 B 的实际位置 / Actual position of item B."""


@dataclass(frozen=True)
class SequenceConstraint:
    """顺序约束 / Sequence constraint.

    验证装载顺序满足规定的先后关系。检查每条顺序限制，
    确保先装载的货物确实排在后装载的货物之前。
    Validates that loading sequence satisfies required ordering.
    Checks each sequence limit to ensure that the predecessor
    item is indeed loaded before the successor.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "sequence"
    """约束名称前缀 / Constraint name prefix."""

    def check_sequence(
        self,
        *,
        limits: tuple[SequenceLimit, ...],
        loading_order: dict[str, int],
    ) -> tuple[SequenceViolation, ...]:
        """检查装载顺序是否满足所有限制。

        Check whether loading sequence satisfies all limits.

        Args:
            limits: 顺序限制列表。/ Sequence limit list.
            loading_order: 货物装载顺序映射，键为货物标识，
                值为装载顺序位置。/
                Loading order mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[SequenceViolation] = []
        for lim in limits:
            pos_a = loading_order.get(lim.item_a)
            pos_b = loading_order.get(lim.item_b)
            if pos_a is None or pos_b is None:
                continue
            if not lim.is_satisfied(pos_a, pos_b):
                violations.append(
                    SequenceViolation(
                        violated_limit=lim,
                        actual_position_a=pos_a,
                        actual_position_b=pos_b,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        limits: tuple[SequenceLimit, ...],
        loading_order: dict[str, int],
    ) -> bool:
        """检查顺序约束是否可行。

        Check whether sequence constraints are feasible.

        Args:
            limits: 顺序限制列表。/ Sequence limit list.
            loading_order: 装载顺序映射。/ Loading order mapping.

        Returns:
            所有顺序限制均满足时返回 True。
            True if all sequence limits are satisfied.
        """
        return (
            len(
                self.check_sequence(
                    limits=limits,
                    loading_order=loading_order,
                )
            )
            == 0
        )

    def required_before(
        self,
        *,
        limits: tuple[SequenceLimit, ...],
        item_type: str,
    ) -> tuple[str, ...]:
        """获取必须在指定货物之前装载的货物类型。

        Get cargo types that must be loaded before a specific type.

        Args:
            limits: 顺序限制列表。/ Sequence limit list.
            item_type: 货物类型。/ Cargo type.

        Returns:
            先装载的货物类型元组。/ Tuple of predecessor types.
        """
        predecessors: list[str] = []
        for lim in limits:
            if lim.is_before and lim.item_b == item_type:
                predecessors.append(lim.item_a)
            elif lim.is_after and lim.item_a == item_type:
                predecessors.append(lim.item_b)
        return tuple(predecessors)

    def required_after(
        self,
        *,
        limits: tuple[SequenceLimit, ...],
        item_type: str,
    ) -> tuple[str, ...]:
        """获取必须在指定货物之后装载的货物类型。

        Get cargo types that must be loaded after a specific type.

        Args:
            limits: 顺序限制列表。/ Sequence limit list.
            item_type: 货物类型。/ Cargo type.

        Returns:
            后装载的货物类型元组。/ Tuple of successor types.
        """
        successors: list[str] = []
        for lim in limits:
            if lim.is_before and lim.item_a == item_type:
                successors.append(lim.item_b)
            elif lim.is_after and lim.item_b == item_type:
                successors.append(lim.item_a)
        return tuple(successors)

    def topological_order(
        self,
        limits: tuple[SequenceLimit, ...],
    ) -> tuple[str, ...] | None:
        """计算拓扑排序的装载顺序。

        Compute topological sort of loading order.

        Args:
            limits: 顺序限制列表。/ Sequence limit list.

        Returns:
            排序后的货物类型元组，存在环时返回 None。
            Sorted cargo type tuple, or None if cycle exists.
        """
        predecessors: dict[str, set[str]] = {}
        successors: dict[str, set[str]] = {}
        all_types: set[str] = set()
        for lim in limits:
            pred = lim.predecessor()
            succ = lim.successor()
            all_types.add(pred)
            all_types.add(succ)
            predecessors.setdefault(succ, set()).add(pred)
            successors.setdefault(pred, set()).add(succ)
        ready = [t for t in all_types if t not in predecessors]
        result: list[str] = []
        while ready:
            node = ready.pop(0)
            result.append(node)
            for succ in successors.get(node, set()):
                pred_set = predecessors.get(succ, set())
                pred_set.discard(node)
                if not pred_set:
                    ready.append(succ)
        if len(result) != len(all_types):
            return None
        return tuple(result)
