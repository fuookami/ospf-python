"""三元组对偶求解器支持 / Triad dual solver support.

为线性三元组模型提供对偶求解支持。
Provides dual solving support for linear triad models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )


class TriadDualSolverSupport:
    """三元组对偶求解器支持 / Triad dual solver support.

    辅助从线性三元组模型中提取对偶信息。
    Assists in extracting dual information from linear
    triad models.

    Methods:
        extract_dual_values: 提取对偶值 / Extract dual values.
    """

    @staticmethod
    def extract_dual_values(
        model: LinearTriadModel,
        dual_solution: dict[str, float],
    ) -> dict[str, float]:
        """提取约束的对偶值 / Extract dual values for constraints.

        Args:
            model: 线性三元组模型 / The linear triad model.
            dual_solution: 原始对偶解 / The raw dual solution.

        Returns:
            约束名到对偶值的映射 / Mapping from constraint
            names to dual values.
        """
        result: dict[str, float] = {}
        for name in model.constraints:
            result[name] = dual_solution.get(name, 0.0)
        return result
