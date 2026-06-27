"""约束检查器 / Constraint checker.

检查二维装箱方案是否满足约束条件。
Checks whether a 2D packing scheme satisfies constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
    ConstraintBase,
    ConstraintType,
)
from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import (
    GeometricConstraint,
)
from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import (
    WeightConstraint,
)
from ospf_python.framework.bpp2d.domain.item.error.bpp2d_errors import (
    Bpp2dErrors,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import (
    Failed,
    Ok,
    Result,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp2d.domain.item.model.packing_result import (
        PackingResult,
    )


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

    检查装箱结果是否满足几何约束和重量约束。
    Checks whether packing results satisfy geometric
    and weight constraints.

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
            tolerance: 容差，默认 1e-9 /
                Tolerance, default 1e-9.

        Returns:
            检查器实例 / ConstraintChecker instance.
        """
        return ConstraintChecker(tolerance=tolerance)

    def check(
        self,
        *,
        constraint: ConstraintBase,
        placed: tuple[PackingResult, ...],
        item_weights: dict[str, float],
    ) -> Result[CheckResult, str, Err[str]]:
        """检查单个约束 / Check a single constraint.

        Args:
            constraint: 待检查约束 / Constraint to check.
            placed: 已放置物品结果 / Placed results.
            item_weights: 物品权重映射 /
                Item weight mapping.

        Returns:
            检查结果或错误 / Check result or error.
        """
        if constraint.constraint_type == (ConstraintType.GEOMETRIC):
            return self._check_geometric(
                constraint=constraint,
                placed=placed,
            )
        if constraint.constraint_type == (ConstraintType.WEIGHT):
            return self._check_weight(
                constraint=constraint,
                placed=placed,
                item_weights=item_weights,
            )
        return Ok(CheckResult.ok())

    def check_all(
        self,
        *,
        constraints: tuple[ConstraintBase, ...],
        placed: tuple[PackingResult, ...],
        item_weights: dict[str, float],
    ) -> Result[tuple[CheckResult, ...], str, Err[str]]:
        """检查所有约束 / Check all constraints.

        Args:
            constraints: 所有约束 / All constraints.
            placed: 已放置物品结果 / Placed results.
            item_weights: 物品权重映射 /
                Item weight mapping.

        Returns:
            所有检查结果或错误 / All results or error.
        """
        results: list[CheckResult] = []
        for c in constraints:
            result = self.check(
                constraint=c,
                placed=placed,
                item_weights=item_weights,
            )
            if result.is_failed():
                return result
            results.append(result.unwrap())
        return Ok(tuple(results))

    def _check_geometric(
        self,
        *,
        constraint: ConstraintBase,
        placed: tuple[PackingResult, ...],
    ) -> Result[CheckResult, str, Err[str]]:
        """检查几何约束 / Check geometric constraint.

        Args:
            constraint: 几何约束 / Geometric constraint.
            placed: 已放置结果 / Placed results.

        Returns:
            检查结果 / Check result.
        """
        assert isinstance(constraint, GeometricConstraint)
        for p in placed:
            if not constraint.applies_to(p.item_key):
                continue
            if not constraint.check_placement(
                x=p.x,
                y=p.y,
                width=p.placed_width,
                height=p.placed_height,
            ):
                return Ok(
                    CheckResult.fail(
                        message=(
                            f"物品 {p.item_key} 放置 "
                            f"({p.x},{p.y}) 违反几何约束 "
                            f"{constraint.constraint_key} / "
                            f"Item {p.item_key} at "
                            f"({p.x},{p.y}) violates "
                            f"geometric constraint "
                            f"{constraint.constraint_key}"
                        ),
                    )
                )
        return Ok(CheckResult.ok())

    def _check_weight(
        self,
        *,
        constraint: ConstraintBase,
        placed: tuple[PackingResult, ...],
        item_weights: dict[str, float],
    ) -> Result[CheckResult, str, Err[str]]:
        """检查重量约束 / Check weight constraint.

        Args:
            constraint: 重量约束 / Weight constraint.
            placed: 已放置结果 / Placed results.
            item_weights: 物品权重映射 /
                Item weight mapping.

        Returns:
            检查结果 / Check result.
        """
        assert isinstance(constraint, WeightConstraint)
        total_weight = 0.0
        for p in placed:
            if not constraint.applies_to(p.item_key):
                continue
            total_weight += item_weights.get(p.item_key, 0.0)
        if not constraint.check_weight(total_weight):
            return Ok(
                CheckResult.fail(
                    message=(
                        f"总重量 {total_weight:.2f} 超出限制 "
                        f"{constraint.max_weight:.2f} / "
                        f"Total weight {total_weight:.2f} "
                        f"exceeds limit "
                        f"{constraint.max_weight:.2f}"
                    ),
                )
            )
        return Ok(CheckResult.ok())

    def validate_solution(
        self,
        *,
        constraints: tuple[ConstraintBase, ...],
        placed: tuple[PackingResult, ...],
        item_weights: dict[str, float],
    ) -> Result[bool, str, Err[str]]:
        """验证完整方案 / Validate complete solution.

        检查所有约束并汇总结果。
        Checks all constraints and aggregates results.

        Args:
            constraints: 所有约束 / All constraints.
            placed: 已放置结果 / Placed results.
            item_weights: 物品权重映射 /
                Item weight mapping.

        Returns:
            全部满足返回 Ok(True)，否则返回失败。
            Ok(True) if all satisfied, failure otherwise.
        """
        result = self.check_all(
            constraints=constraints,
            placed=placed,
            item_weights=item_weights,
        )
        if result.is_failed():
            return result
        for r in result.unwrap():
            if not r.satisfied:
                return Failed(
                    Err(
                        _code=(Bpp2dErrors.BOUNDARY_VIOLATED.value),
                        _message=(
                            f"方案验证失败: {r.message} / "
                            f"Solution validation failed: "
                            f"{r.message}"
                        ),
                    )
                )
        return Ok(True)
