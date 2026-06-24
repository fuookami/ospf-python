"""求解值验证 / Solve value validation.

提供求解值的有效性验证功能。
Provides validity checking for solve values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.value.solve_value import (
        SolveValue,
    )


@dataclass(frozen=True)
class SolveValueValidation:
    """求解值验证结果 / Solve value validation result.

    冻结数据类，记录验证过程中发现的问题。
    Frozen dataclass recording issues found during
    validation.

    Attributes:
        is_valid: 是否有效 / Whether valid.
        issues: 问题列表 / List of issues.
    """

    is_valid: bool = True
    """是否有效 / Whether valid."""

    issues: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """问题列表 / List of issues."""

    @staticmethod
    def validate(
        solve_value: SolveValue,
        *,
        allow_nan: bool = False,
        allow_inf: bool = False,
    ) -> SolveValueValidation:
        """验证求解值 / Validate a solve value.

        Args:
            solve_value: 要验证的求解值 / Solve value to
                validate.
            allow_nan: 是否允许 NaN / Whether NaN is
                allowed.
            allow_inf: 是否允许 Inf / Whether Inf is
                allowed.

        Returns:
            验证结果 / Validation result.
        """
        issues: list[str] = []
        for name, val in solve_value.values.items():
            if math.isnan(val) and not allow_nan:
                issues.append(f"Variable '{name}' is NaN.")
            if math.isinf(val) and not allow_inf:
                issues.append(f"Variable '{name}' is Inf.")
        return SolveValueValidation(
            is_valid=len(issues) == 0,
            issues=tuple(issues),
        )
