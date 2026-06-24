"""二次四元组弹性构建器 / Quadratic tetrad elastic builder.

为二次约束提供弹性变量支持。
Provides elastic variable support for quadratic constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.quadratic_tetrad_model import (
        QuadraticTetradModel,
    )


class QuadraticTetradElasticBuilder:
    """二次四元组弹性构建器 / Quadratic tetrad elastic builder.

    为硬约束添加弹性变量，使其可以在一定范围内被违反。
    Adds elastic variables to hard constraints so they can
    be violated within a certain range.

    Methods:
        add_elastic: 为指定约束添加弹性变量 / Add elastic
            variables to a specified constraint.
    """

    @staticmethod
    def add_elastic(
        model: QuadraticTetradModel,
        constraint_name: str,
        penalty: float = 1.0,
    ) -> None:
        """为指定约束添加弹性变量 / Add elastic variables.

        Args:
            model: 二次四元组模型 / The quadratic tetrad model.
            constraint_name: 约束名称 / The constraint name.
            penalty: 弹性惩罚系数 / The elastic penalty
                coefficient.
        """
        if constraint_name not in model.linear_constraints:
            return
        row = model.linear_constraints[constraint_name]
        elastic_name = f"elastic_{constraint_name}"
        row[elastic_name] = penalty
