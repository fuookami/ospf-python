"""CSP1D 解恢复服务 / CSP1D solution recovery service."""

from __future__ import annotations

from collections.abc import Mapping
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
        *,
        material_lengths: Mapping[str, float] | None = None,
    ) -> Result[Csp1dSolution, str, Error[Any]]:
        """从变量值恢复解决方案 / Recover solution from variable values.

        Args:
            variable_values: 变量名-值对 / Variable name-value pairs.
            material_names: 材料名称列表 / Material name list.
            plan_names: 切割方案名称列表 / Cutting plan name list.
            material_lengths: 材料键到长度的映射。给出时利用率按
                "已用长度 / 消耗长度" 精确计算；不给时只能判断有无余料。
                Map from material key to its length. When given, utilization is
                "used length / consumed length"; otherwise only "waste or not"
                can be reported.

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
                # 容差只筛噪声，不能把噪声抬成 1：round(1e-5) 是 0，原来的 max(1, ...)
                # 会给求解器根本没有选中的变量记 1 件。
                # The tolerance only filters noise; it must not promote noise to one unit:
                # round(1e-5) is 0, and the old max(1, ...) recorded one unit for a variable the
                # solver never selected.
                qty = round(val) if val > self._tolerance else 0
                if qty >= 1:
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

        utilization = self._utilization(
            assignments=assignments,
            total_waste=total_waste,
            material_lengths=material_lengths,
        )

        return Ok(
            Csp1dSolution(
                assignments=tuple(assignments),
                total_waste=total_waste,
                utilization=max(0.0, min(1.0, utilization)),
            )
        )

    def _utilization(
        self,
        *,
        assignments: list[Csp1dAssignment],
        total_waste: float,
        material_lengths: Mapping[str, float] | None,
    ) -> float:
        """计算材料利用率 / Compute material utilization.

        余料是长度、quantity 是根数，两者不能直接相除。旧实现算的是
        ``1 - total_waste / 根数``，凡有余料必为负、被 clamp 成 0.0，
        使利用率退化成"没余料 1.0、有余料 0.0"的二值。
        Waste is a length and quantity is a bar count, so they cannot be divided directly. The
        old code computed ``1 - total_waste / bar_count``, which went negative for any waste and
        was clamped to 0.0, degrading utilization to "1.0 with no waste, 0.0 otherwise".

        Args:
            assignments: 已恢复的分配 / Recovered assignments.
            total_waste: 总余料长度 / Total waste length.
            material_lengths: 材料长度映射，可缺省 / Material length map, optional.

        Returns:
            利用率，不可计算时返回 0.0 / Utilization, 0.0 when it cannot be computed.
        """
        if not material_lengths:
            # 没有长度就只能判断"有没有余料"：这是当前输入能给出的最准确结论。
            # Without lengths the only sound statement is whether any waste exists.
            return 0.0 if total_waste > 0.0 else 1.0

        used = 0.0
        consumed = 0.0
        for assignment in assignments:
            length = material_lengths.get(assignment.material)
            if length is None or length <= 0.0:
                return 0.0
            consumed += length * assignment.quantity
            used += max(0.0, length - assignment.waste) * assignment.quantity
        if consumed <= 0.0:
            return 0.0
        return max(0.0, min(1.0, used / consumed))
