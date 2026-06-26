"""CSP1D 解恢复服务 / CSP1D solution recovery service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Ok, Result, failed_from_code

if TYPE_CHECKING:
    from ospf_python.utils.error.error import Error


class Csp1dRecovery:
    """解恢复服务 / Solution recovery service.

    从求解器的原始变量值中恢复结构化的切割分配方案。
    Recovers structured cutting assignments from
    raw solver variable values.

    Attributes:
        _tolerance: 整数判定容差 / Integer determination tolerance.
    """

    def __init__(
        self,
        tolerance: float = 1e-6,
    ) -> None:
        """初始化恢复服务 / Initialize recovery service.

        Args:
            tolerance: 整数判定容差 / Integer determination tolerance.
        """
        self._tolerance = tolerance

    def recover(
        self,
        variable_values: tuple[tuple[str, float], ...],
        material_names: tuple[str, ...],
        plan_names: tuple[str, ...],
    ) -> Result[Csp1dSolution, str, Error[Any]]:
        """从变量值恢复解决方案 / Recover solution from variable values.

        Args:
            variable_values: 变量名-值对 / Variable name-value pairs.
            material_names: 材料名称列表 / Material name list.
            plan_names: 切割方案名称列表 / Cutting plan name list.

        Returns:
            恢复的解决方案 / Recovered solution.
        """
        assignments: list[Csp1dAssignment] = []
        total_waste: float = 0.0

        value_map = dict(variable_values)
        for mat in material_names:
            for plan in plan_names:
                key = f"x_{mat}_{plan}"
                val = value_map.get(key, 0.0)
                if val > self._tolerance:
                    qty = max(1, round(val))
                    waste_key = f"w_{mat}_{plan}"
                    waste = value_map.get(waste_key, 0.0)
                    assignments.append(
                        Csp1dAssignment(
                            material=mat,
                            cutting_plan=plan,
                            quantity=qty,
                            waste=waste,
                        )
                    )
                    total_waste += waste * qty

        if not assignments:
            return failed_from_code(
                ErrorCode.APPLICATION_ERROR,
                "无法从变量值恢复有效分配 / "
                "Cannot recover valid assignments "
                "from variable values",
            )

        sum(a.quantity for a in assignments)
        total_material = sum(a.quantity for a in assignments)
        utilization = 1.0 - total_waste / max(total_material, 1.0)

        return Ok(
            Csp1dSolution(
                assignments=tuple(assignments),
                total_waste=total_waste,
                utilization=max(0.0, min(1.0, utilization)),
            )
        )
