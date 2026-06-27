"""解验证器 / Solution validator.

BPP1D 中装箱解的验证逻辑。
Packing solution validation logic in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp1d.domain.constraint.service.constraint_checker import (
    ConstraintChecker,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
        Constraint,
    )
    from ospf_python.framework.bpp1d.domain.item.model.item import Item
    from ospf_python.framework.bpp1d.domain.solution.model.solution import (
        Solution,
    )


@dataclass(frozen=True)
class ValidationReport:
    """验证报告 / Validation report.

    描述解验证的结果。
    Describes the result of solution validation.

    Attributes:
        valid: 是否有效 / Whether valid.
        errors: 错误列表 / Error list.
    """

    valid: bool
    """是否有效 / Whether valid."""

    errors: tuple[str, ...] = ()
    """错误列表，默认空 / Error list, default empty."""

    @staticmethod
    def ok() -> ValidationReport:
        """创建成功报告 / Create ok report.

        Returns:
            有效报告 / Valid report.
        """
        return ValidationReport(valid=True)

    @staticmethod
    def fail(
        *,
        errors: tuple[str, ...],
    ) -> ValidationReport:
        """创建失败报告 / Create fail report.

        Args:
            errors: 错误列表 / Error list.

        Returns:
            无效报告 / Invalid report.
        """
        return ValidationReport(valid=False, errors=errors)


@dataclass(frozen=True)
class SolutionValidator:
    """解验证器 / Solution validator.

    验证装箱解的完整性和约束满足情况。
    Validates solution integrity and constraint satisfaction.

    Attributes:
        checker: 约束检查器 / Constraint checker.
    """

    checker: ConstraintChecker = None
    """约束检查器 / Constraint checker."""

    def __post_init__(self) -> None:
        """初始化后处理 / Post-init handler.

        设置默认检查器。
        Sets default checker.
        """
        if self.checker is None:
            object.__setattr__(
                self,
                "checker",
                ConstraintChecker.create(),
            )

    @staticmethod
    def create(
        *,
        checker: ConstraintChecker | None = None,
    ) -> SolutionValidator:
        """创建验证器 / Create validator.

        Args:
            checker: 约束检查器，默认新建 /
                Constraint checker, default new.

        Returns:
            验证器实例 / SolutionValidator instance.
        """
        return SolutionValidator(
            checker=checker or ConstraintChecker.create(),
        )

    def validate(
        self,
        *,
        solution: Solution,
        items: tuple[Item, ...],
        constraints: tuple[Constraint, ...],
    ) -> ValidationReport:
        """验证解 / Validate solution.

        检查解的完整性、容量和约束满足情况。
        Checks solution integrity, capacity, and constraint
        satisfaction.

        Args:
            solution: 待验证解 / Solution to validate.
            items: 所有物品 / All items.
            constraints: 所有约束 / All constraints.

        Returns:
            验证报告 / Validation report.
        """
        errors: list[str] = []

        capacity_errors = self._check_capacity(solution)
        errors.extend(capacity_errors)

        dup_errors = self._check_duplicates(solution)
        errors.extend(dup_errors)

        constraint_errors = self._check_constraints(
            solution=solution,
            items=items,
            constraints=constraints,
        )
        errors.extend(constraint_errors)

        if errors:
            return ValidationReport.fail(errors=tuple(errors))
        return ValidationReport.ok()

    def _check_capacity(
        self,
        solution: Solution,
    ) -> list[str]:
        """检查容量 / Check capacity.

        Args:
            solution: 待检查解 / Solution to check.

        Returns:
            错误列表 / Error list.
        """
        errors: list[str] = []
        for bin_ in solution.bins:
            if bin_.used_capacity > bin_.capacity + 1e-9:
                errors.append(
                    f"Bin '{bin_.bin_key}' over capacity: "
                    f"{bin_.used_capacity:.2f} > "
                    f"{bin_.capacity:.2f}"
                )
        return errors

    def _check_duplicates(
        self,
        solution: Solution,
    ) -> list[str]:
        """检查重复放置 / Check duplicate placement.

        Args:
            solution: 待检查解 / Solution to check.

        Returns:
            错误列表 / Error list.
        """
        seen: set[str] = set()
        errors: list[str] = []
        for bin_ in solution.bins:
            for item in bin_.items:
                uid = f"{bin_.bin_key}:{item.item_key}"
                if uid in seen:
                    errors.append(f"Duplicate placement: {uid}")
                seen.add(uid)
        return errors

    def _check_constraints(
        self,
        *,
        solution: Solution,
        items: tuple[Item, ...],
        constraints: tuple[Constraint, ...],
    ) -> list[str]:
        """检查约束 / Check constraints.

        Args:
            solution: 待检查解 / Solution to check.
            items: 所有物品 / All items.
            constraints: 所有约束 / All constraints.

        Returns:
            错误列表 / Error list.
        """
        errors: list[str] = []
        for bin_ in solution.bins:
            results = self.checker.check_all(
                constraints=constraints,
                bin_=bin_,
                items=items,
            )
            for result in results:
                if not result.satisfied:
                    errors.append(f"Bin '{bin_.bin_key}': {result.message}")
        return errors
