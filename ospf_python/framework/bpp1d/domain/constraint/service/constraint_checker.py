"""约束检查器 / Constraint checker.

BPP1D 中装箱约束的检查逻辑。
Packing constraint checking logic in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    ConstraintType,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
        Constraint,
    )
    from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
    from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class CheckResult:
    """检查结果 / Check result.

    描述约束检查的结果。
    Describes the result of a constraint check.

    Attributes:
        satisfied: 是否满足 / Whether satisfied.
        message: 结果消息 / Result message.
    """

    satisfied: bool
    """是否满足 / Whether satisfied."""

    message: str = ""
    """结果消息，默认空 / Result message, default empty."""

    @staticmethod
    def ok() -> CheckResult:
        """创建成功结果 / Create ok result.

        Returns:
            满足约束的结果 / Satisfied result.
        """
        return CheckResult(satisfied=True)

    @staticmethod
    def fail(*, message: str) -> CheckResult:
        """创建失败结果 / Create fail result.

        Args:
            message: 失败原因 / Failure reason.

        Returns:
            不满足约束的结果 / Unsatisfied result.
        """
        return CheckResult(satisfied=False, message=message)


@dataclass(frozen=True)
class ConstraintChecker:
    """约束检查器 / Constraint checker.

    检查装箱方案是否满足约束条件。
    Checks whether a packing scheme satisfies constraints.

    Attributes:
        tolerance: 数值容差 / Numeric tolerance.
    """

    tolerance: float = 1e-9
    """数值容差 / Numeric tolerance."""

    @staticmethod
    def create(
        *,
        tolerance: float = 1e-9,
    ) -> ConstraintChecker:
        """创建检查器 / Create checker.

        Args:
            tolerance: 容差，默认 1e-9 / Tolerance, default 1e-9.

        Returns:
            检查器实例 / ConstraintChecker instance.
        """
        return ConstraintChecker(tolerance=tolerance)

    def check(
        self,
        *,
        constraint: Constraint,
        bin_: Bin,
        items: tuple[Item, ...],
    ) -> CheckResult:
        """检查约束 / Check constraint.

        Args:
            constraint: 待检查约束 / Constraint to check.
            bin_: 目标箱子 / Target bin.
            items: 所有可用物品 / All available items.

        Returns:
            检查结果 / Check result.
        """
        if constraint.constraint_type == ConstraintType.WEIGHT_LIMIT:
            return self._check_weight_limit(
                constraint=constraint,
                bin_=bin_,
            )
        if constraint.constraint_type == ConstraintType.ITEM_EXCLUSION:
            return self._check_item_exclusion(
                constraint=constraint,
                bin_=bin_,
            )
        if constraint.constraint_type == ConstraintType.ITEM_GROUPING:
            return self._check_item_grouping(
                constraint=constraint,
                bin_=bin_,
            )
        return CheckResult.ok()

    def check_all(
        self,
        *,
        constraints: tuple[Constraint, ...],
        bin_: Bin,
        items: tuple[Item, ...],
    ) -> tuple[CheckResult, ...]:
        """检查所有约束 / Check all constraints.

        Args:
            constraints: 所有约束 / All constraints.
            bin_: 目标箱子 / Target bin.
            items: 所有可用物品 / All available items.

        Returns:
            所有检查结果 / All check results.
        """
        return tuple(
            self.check(
                constraint=c,
                bin_=bin_,
                items=items,
            )
            for c in constraints
        )

    def _check_weight_limit(
        self,
        *,
        constraint: Constraint,
        bin_: Bin,
    ) -> CheckResult:
        """检查重量限制 / Check weight limit.

        Args:
            constraint: 重量限制约束 / Weight limit constraint.
            bin_: 目标箱子 / Target bin.

        Returns:
            检查结果 / Check result.
        """
        constraint_items = tuple(
            item for item in bin_.items if item.item_key in constraint.item_keys
        )
        total = sum(item.weight for item in constraint_items)
        if total <= constraint.max_value + self.tolerance:
            return CheckResult.ok()
        return CheckResult.fail(
            message=(f"Weight {total:.2f} exceeds limit {constraint.max_value:.2f}"),
        )

    def _check_item_exclusion(
        self,
        *,
        constraint: Constraint,
        bin_: Bin,
    ) -> CheckResult:
        """检查物品互斥 / Check item exclusion.

        Args:
            constraint: 互斥约束 / Exclusion constraint.
            bin_: 目标箱子 / Target bin.

        Returns:
            检查结果 / Check result.
        """
        found_keys = tuple(
            item.item_key
            for item in bin_.items
            if item.item_key in constraint.item_keys
        )
        if len(found_keys) <= 1:
            return CheckResult.ok()
        return CheckResult.fail(
            message=(f"Exclusion violated: {found_keys} in same bin"),
        )

    def _check_item_grouping(
        self,
        *,
        constraint: Constraint,
        bin_: Bin,
    ) -> CheckResult:
        """检查物品分组 / Check item grouping.

        确保同组物品装入同一箱子。
        Ensures grouped items are in the same bin.

        Args:
            constraint: 分组约束 / Grouping constraint.
            bin_: 目标箱子 / Target bin.

        Returns:
            检查结果 / Check result.
        """
        bin_keys = frozenset(item.item_key for item in bin_.items)
        group_keys = frozenset(constraint.item_keys)
        in_bin = bin_keys & group_keys
        if not in_bin or in_bin == group_keys:
            return CheckResult.ok()
        if 0 < len(in_bin) < len(group_keys):
            return CheckResult.fail(
                message=(
                    f"Grouping violated: only "
                    f"{in_bin} in bin, expected "
                    f"all of {group_keys}"
                ),
            )
        return CheckResult.ok()
