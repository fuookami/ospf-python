"""平衡约束 / Balance constraint.

确保装载方案满足飞机重心平衡要求。
Ensures that stowage plans satisfy aircraft CG balance
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.stowage_balance import (
    StowageBalance,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.balance_limit import (
        BalanceLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class BalanceViolation:
    """平衡违反记录 / Balance violation record.

    记录力矩超出允许范围的信息。
    Records moment exceeding allowable range information.

    Attributes:
        axis: 力矩轴 / Moment axis.
        current_moment: 当前力矩 / Current moment.
        limit: 平衡限制 / Balance limit.
        violation_amount: 违反量 / Violation amount.
    """

    axis: str = ""
    """力矩轴 / Moment axis."""

    current_moment: float = 0.0
    """当前力矩（千克·米）/ Current moment (kg*m)."""

    limit: BalanceLimit = None  # type: ignore[assignment]
    """平衡限制 / Balance limit."""

    violation_amount: float = 0.0
    """违反量 / Violation amount."""


@dataclass(frozen=True)
class BalanceConstraint:
    """平衡约束 / Balance constraint.

    验证装载方案的力矩在允许范围内。分别检查横向和纵向
    力矩，确保飞机重心不会偏离安全区域。
    Validates that moments of a stowage plan are within allowable
    ranges. Checks lateral and longitudinal moments separately
    to ensure the aircraft CG does not deviate from safe zones.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        lateral_limit: 横向力矩限制 /
            Lateral moment limit.
        longitudinal_limit: 纵向力矩限制 /
            Longitudinal moment limit.
    """

    constraint_name_prefix: str = "balance"
    """约束名称前缀 / Constraint name prefix."""

    lateral_limit: BalanceLimit = None  # type: ignore[assignment]
    """横向力矩限制 / Lateral moment limit."""

    longitudinal_limit: BalanceLimit = None  # type: ignore[assignment]
    """纵向力矩限制 / Longitudinal moment limit."""

    @staticmethod
    def create(
        *,
        lateral_limit: BalanceLimit,
        longitudinal_limit: BalanceLimit,
    ) -> BalanceConstraint:
        """创建平衡约束。

        Create balance constraint.

        Args:
            lateral_limit: 横向力矩限制。/ Lateral moment limit.
            longitudinal_limit: 纵向力矩限制。/
                Longitudinal moment limit.

        Returns:
            约束实例。/ Constraint instance.
        """
        return BalanceConstraint(
            lateral_limit=lateral_limit,
            longitudinal_limit=longitudinal_limit,
        )

    def compute_balance(
        self,
        item_placements: tuple[tuple[StowageItem, StowagePosition], ...],
    ) -> StowageBalance:
        """计算装载方案的平衡指标。

        Compute balance metrics for a stowage plan.

        Args:
            item_placements: 货物及其位置的配对列表。/
                List of item-position pairs.

        Returns:
            平衡指标。/ Balance metrics.
        """
        lateral = 0.0
        longitudinal = 0.0
        total_weight = 0.0
        for item, pos in item_placements:
            lateral += pos.lateral_moment(item.weight)
            longitudinal += pos.longitudinal_moment(item.weight)
            total_weight += item.weight
        return StowageBalance.from_moments(
            lateral_moment=lateral,
            longitudinal_moment=longitudinal,
            total_weight=total_weight,
        )

    def check_balance(
        self,
        balance: StowageBalance,
    ) -> tuple[BalanceViolation, ...]:
        """检查平衡指标是否违反限制。

        Check whether balance metrics violate limits.

        Args:
            balance: 平衡指标。/ Balance metrics.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[BalanceViolation] = []
        lat_violation = self.lateral_limit.violation_amount(
            balance.lateral_moment,
        )
        if lat_violation > 0.0:
            violations.append(
                BalanceViolation(
                    axis="LATERAL",
                    current_moment=balance.lateral_moment,
                    limit=self.lateral_limit,
                    violation_amount=lat_violation,
                )
            )
        lon_violation = self.longitudinal_limit.violation_amount(
            balance.longitudinal_moment,
        )
        if lon_violation > 0.0:
            violations.append(
                BalanceViolation(
                    axis="LONGITUDINAL",
                    current_moment=balance.longitudinal_moment,
                    limit=self.longitudinal_limit,
                    violation_amount=lon_violation,
                )
            )
        return tuple(violations)

    def is_feasible(
        self,
        balance: StowageBalance,
    ) -> bool:
        """检查平衡是否可行。

        Check whether balance is feasible.

        Args:
            balance: 平衡指标。/ Balance metrics.

        Returns:
            所有力矩均在限制内时返回 True。
            True if all moments are within limits.
        """
        return len(self.check_balance(balance)) == 0

    def lateral_violation(
        self,
        balance: StowageBalance,
    ) -> float:
        """获取横向违反量。

        Get lateral violation amount.

        Args:
            balance: 平衡指标。/ Balance metrics.

        Returns:
            横向力矩违反量。/ Lateral moment violation amount.
        """
        return self.lateral_limit.violation_amount(
            balance.lateral_moment,
        )

    def longitudinal_violation(
        self,
        balance: StowageBalance,
    ) -> float:
        """获取纵向违反量。

        Get longitudinal violation amount.

        Args:
            balance: 平衡指标。/ Balance metrics.

        Returns:
            纵向力矩违反量。/ Longitudinal moment violation amount.
        """
        return self.longitudinal_limit.violation_amount(
            balance.longitudinal_moment,
        )
